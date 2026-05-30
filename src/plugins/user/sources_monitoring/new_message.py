import logging

from peewee import DoesNotExist
from telethon import errors as telethon_errors

from alerts.regex_rule import check_message_by_regex_alert_rule
from common.notifier_registry import get_user_error_notifier
from models import MessageHistory, Source
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageCleanedFullyError,
    MessageFilteredError,
    MessageForwardsRestrictedError,
    MessageIdInvalidError,
    MessageRepeatedError,
    MessageTooLongError,
    MessageUnknownError,
)
from plugins.user.sources_monitoring.common import (
    add_header,
    cut_long_message,
    get_filter_id_or_none,
    is_media_message_with_caption,
    is_monitored_filter,
    get_reply_to,
    set_blocking,
)
from plugins.user.types import Operation
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.dump import dump_message
from plugins.user.utils.telethon_helpers import (
    copy_message,
    forward_messages,
    get_fwd_origin,
    msg_text,
    send_album_with_entities,
    tl_message_to_dict,
)

NEW = Operation.NEW

log = logging.getLogger(__name__)


# Alias для обратной совместимости с тестами и processing_unread_messages_job
async def new_message(client, message) -> None:
    """Wrapper: обработать одиночное сообщение (совместимость с тестами)."""
    await handle_new_messages(client, [message])


async def on_new_message(event):
    """
    Telethon event handler для новых сообщений из источников.
    Регистрируется в main.py через client.add_event_handler.
    """
    if not await is_monitored_filter(event):
        return

    message = event.message
    client = event.client

    # Медиа-группы собираются буфером, одиночные — сразу
    if message.grouped_id is not None:
        from clients import album_collector
        await album_collector.add(
            chat_id=message.chat_id,
            grouped_id=message.grouped_id,
            message=message,
            callback=lambda msgs: handle_new_messages(client, msgs),
        )
    else:
        await handle_new_messages(client, [message])


async def handle_new_messages(client, source_messages: list) -> None:  # noqa: C901
    """
    Основная логика обработки нового сообщения (одиночного или альбома).
    Вызывается и из event handler'а, и из processing_unread_messages_job.
    """
    first_msg = source_messages[0]
    is_album = len(source_messages) > 1

    log.debug(
        "Источник %s отправил сообщение %s (album=%s)",
        first_msg.chat_id,
        first_msg.id,
        is_album,
    )
    for msg in source_messages:
        dump_message(message=msg, operation=NEW)

    blocked = None
    source = None
    history: dict[int, MessageHistory] = {}
    exc = None
    try:
        blocked = set_blocking(
            operation=NEW,
            message=first_msg,
            block_value=first_msg.grouped_id or first_msg.id,
        )

        source = Source.get(first_msg.chat_id)

        repeated = False
        filtered = False
        for msg in source_messages:
            repeat_history_id = get_repeated_history_id_or_none(msg)
            filter_id = get_filter_id_or_none(message=msg, source_id=source.id)
            repeated = repeated or bool(repeat_history_id)
            filtered = filtered or bool(filter_id)

            fwd_origin = get_fwd_origin(msg)
            history[msg.id] = MessageHistory(
                source_id=source.id,
                source_message_id=msg.id,
                source_media_group_id=msg.grouped_id,
                source_forward_from_chat_id=fwd_origin[0] if fwd_origin else None,
                source_forward_from_message_id=fwd_origin[1] if fwd_origin else None,
                category_id=source.category_id,
                repeat_history_id=repeat_history_id,
                filter_id=filter_id,
                created_at=msg.date,
                data=dict(first_message=dict(source=tl_message_to_dict(msg))),
            )

        if repeated:
            raise MessageRepeatedError(operation=NEW, message=first_msg)

        if filtered:
            raise MessageFilteredError(operation=NEW, message=first_msg)

        if not is_album:
            category_messages = [
                await new_one_message(client, first_msg, source)
            ]
            log.info(
                "Источник %s отправил сообщение %s → категория %s",
                first_msg.chat_id, first_msg.id, source.category_id,
            )
        else:
            category_messages = await new_media_group_messages(
                client, source_messages, source
            )
            log.info(
                "Источник %s медиа-группа %s → категория %s (%d сообщений)",
                first_msg.chat_id, first_msg.grouped_id, source.category_id,
                len(source_messages),
            )

        for src_msg, cat_msg in zip(source_messages, category_messages):
            history_obj = history[src_msg.id]
            history_obj.category_message_rewritten = source.is_rewrite
            history_obj.category_message_id = cat_msg.id
            history_obj.category_media_group_id = cat_msg.grouped_id
            history_obj.data["first_message"]["category"] = tl_message_to_dict(cat_msg)

            await check_message_by_regex_alert_rule(
                category_id=history_obj.category_id,
                message=cat_msg,
            )

    except MessageBaseError as e:
        exc = e
    except telethon_errors.MessageIdInvalidError as error:
        exc = MessageIdInvalidError(operation=NEW, message=first_msg, error=error)
    except telethon_errors.ChatForwardsRestrictedError:
        exc = MessageForwardsRestrictedError(operation=NEW, message=first_msg)
        if source and not source.is_rewrite:
            await get_user_error_notifier().report(
                f"⚠ Источник {source.title or first_msg.chat_id} запрещает пересылку. "
                "Установите режим перепечатывания сообщений."
            )
    except telethon_errors.MessageTooLongError as error:
        exc = MessageTooLongError(operation=NEW, message=first_msg, error=error)
    except telethon_errors.BadRequestError as error:
        exc = MessageBadRequestError(operation=NEW, message=first_msg, error=error)
    except Exception as error:
        exc = MessageUnknownError(operation=NEW, message=first_msg, error=error)
    finally:
        if blocked:
            blocked.remove(value=first_msg.grouped_id or first_msg.id)

        if exc and (history_obj := history.get(first_msg.id)):
            history_obj.data["first_message"]["exception"] = exc.to_dict()

        for history_obj in history.values():
            history_obj.save()

        if source_messages:
            try:
                await client.send_read_acknowledge(
                    first_msg.chat_id,
                    max_id=max(m.id for m in source_messages),
                )
            except Exception:
                pass


def get_repeated_history_id_or_none(message) -> int | None:
    """Проверить, пересылалось ли сообщение раньше (дедупликация)."""
    fwd_origin = get_fwd_origin(message)
    if fwd_origin:
        # Сообщение переслано из другого чата
        source_chat_id, source_message_id = fwd_origin
        forward_from_chat_id, forward_from_message_id = fwd_origin
    else:
        # Обычное сообщение — проверяем по самому сообщению
        source_chat_id = message.chat_id
        source_message_id = message.id
        forward_from_chat_id = message.chat_id
        forward_from_message_id = message.id

    mh: type[MessageHistory] = MessageHistory.alias()
    try:
        history_obj = (
            mh.select(mh.id)
            .where(
                (
                    (
                        (mh.source_id == source_chat_id)
                        & (mh.source_message_id == source_message_id)
                    )
                    | (
                        (mh.source_forward_from_chat_id == forward_from_chat_id)
                        & (mh.source_forward_from_message_id == forward_from_message_id)
                    )
                )
                & (mh.category_message_id != None)  # noqa: E711
            )
            .get()
        )
    except DoesNotExist:
        return None

    return history_obj.id


async def new_one_message(client, message, source: Source, disable_notification: bool = False):
    """
    Переслать или перепечатать одиночное сообщение в категорию.
    """
    if not source.is_rewrite:
        result = await forward_messages(
            client,
            target_chat_id=source.category.id,
            source_chat_id=message.chat_id,
            message_ids=[message.id],
            disable_notification=disable_notification,
        )
        return result[0] if isinstance(result, list) else result

    is_media = is_media_message_with_caption(operation=NEW, message=message)

    cleanup_message(message=message, source=source)

    if not (msg_text(message) or is_media):
        raise MessageCleanedFullyError(operation=NEW, message=message)

    await add_header(client, source=source, message=message)
    cut_long_message(message=message)

    reply_to_id = get_reply_to(message)

    return await copy_message(
        client,
        target_chat_id=source.category.id,
        message=message,
        reply_to=reply_to_id,
        disable_notification=disable_notification,
    )


async def new_media_group_messages(
    client,
    messages: list,
    source: Source,
    disable_notification: bool = False,
) -> list:
    """
    Переслать или перепечатать медиа-группу в категорию.
    """
    if not source.is_rewrite:
        return await forward_messages(
            client,
            target_chat_id=source.category.id,
            source_chat_id=messages[0].chat_id,
            message_ids=[m.id for m in messages],
            disable_notification=disable_notification,
        )

    media_has_caption = False
    for msg in messages:
        if msg_text(msg):
            media_has_caption = True
            cleanup_message(message=msg, source=source)
            await add_header(client, source=source, message=msg)
            cut_long_message(message=msg)

    if not media_has_caption:
        await add_header(client, source=source, message=messages[0])

    return await send_album_with_entities(
        client,
        target_chat_id=source.category.id,
        messages=messages,
        disable_notification=disable_notification,
    )
