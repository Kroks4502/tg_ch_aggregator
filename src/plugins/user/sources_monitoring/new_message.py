import json
import logging

import telethon
from peewee import DoesNotExist
from telethon import events
from telethon.tl import patched, types

from alerts.regex_rule import check_message_by_regex_alert_rule
from clients import user_client
from common.types import MessageEventType
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
    set_blocking,
)
from plugins.user.types import Operation
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.dump import dump_message
from plugins.user.utils.senders import send_error_to_admins

NEW = Operation.NEW
NEW_GROUP = Operation.NEW_GROUP
RECEIVING_MSG_TPL = "Источник %s %s %s"


def is_not_a_group(event: patched.Message):
    return True if event.grouped_id is None else None


# @Client.on_message(custom_filters.monitored_channels & ~filters.service)
@user_client.on(events.NewMessage(func=is_not_a_group))
async def new_message(event: MessageEventType):
    logging.debug(RECEIVING_MSG_TPL, event.chat_id, NEW, event.id)
    dump_message(event=event, operation=NEW)
    await processing_new_messages(
        chat_id=event.chat_id,
        event_id=event.id,
        source_messages=[event.message],
    )


@user_client.on(events.Album())
async def new_group_messages(event: events.Album.Event):
    logging.debug(RECEIVING_MSG_TPL, event.chat_id, NEW_GROUP, event.grouped_id)
    dump_message(event=event, operation=NEW)
    await processing_new_messages(
        chat_id=event.chat_id,
        event_id=event.grouped_id,
        source_messages=event.messages,
    )


async def processing_new_messages(
    chat_id: int,
    event_id: int,
    source_messages: list[patched.Message],
) -> None:  # noqa: C901 todo
    """
    Обработка новых сообщений.

    :param chat_id: ID чата.
    :param event_id: ID сообщения или группы сообщений.
    :param source_messages: Экземпляры сообщений источника.
    """
    blocked = None
    source = None
    history = dict()
    exc = None
    try:
        blocked = set_blocking(
            chat_id=chat_id,
            block_id=event_id,
            operation=NEW,
        )

        source = Source.get(chat_id)

        repeated = False
        filtered = False
        for msg in source_messages:
            if msg.fwd_from:
                repeat_history_id = get_repeated_history_id_or_none(
                    chat_id=msg.fwd_from.from_id.chat_id,
                    message_id=msg.fwd_from.saved_from_msg_id,
                )
            else:
                repeat_history_id = get_repeated_history_id_or_none(
                    chat_id=msg.chat.id,
                    message_id=msg.id,
                )
            repeated = True if repeat_history_id else repeated

            filter_id = get_filter_id_or_none(source_id=source.id, message=msg)
            filtered = True if filter_id else filtered

            history[msg.id] = MessageHistory(
                source_id=source.id,
                source_message_id=msg.id,
                source_media_group_id=msg.grouped_id,
                source_forward_from_chat_id=(
                    msg.fwd_from.from_id if msg.fwd_from else None
                ),
                source_forward_from_message_id=msg.fwd_from.saved_from_msg_id,
                category_id=source.category_id,
                repeat_history_id=repeat_history_id,
                filter_id=filter_id,
                created_at=msg.date,
                data=dict(
                    first_message=dict(
                        source=json.loads(msg.__str__()),
                    ),
                ),
            )

        if repeated:
            raise MessageRepeatedError(chat_id, event_id, NEW)

        if filtered:
            raise MessageFilteredError(chat_id, event_id, NEW)

        if len(source_messages) == 1:
            category_messages = [
                await new_one_message(
                    message=source_messages[0],
                    source=source,
                )
            ]

            logging.info(
                "Источник %s отправил сообщение %s, оно отправлено в категорию %s",
                chat_id,
                event_id,
                source.category_id,
            )
        else:
            category_messages = await new_media_group_messages(
                messages=source_messages,
                source=source,
            )

            logging.info(
                (
                    "Источник %s отправил группу сообщений %s, они отправлены в"
                    " категорию %s"
                ),
                chat_id,
                event_id,
                source.category_id,
            )

        for src_msg, cat_msg in zip(source_messages, category_messages):
            history_obj = history[src_msg.id]
            history_obj.category_message_rewritten = source.is_rewrite
            history_obj.category_message_id = cat_msg.id
            history_obj.category_media_group_id = cat_msg.grouped_id
            history_obj.data["first_message"]["category"] = json.loads(
                cat_msg.__str__()
            )

            await check_message_by_regex_alert_rule(
                category_id=history_obj.category_id,
                message=cat_msg,
            )

    except MessageBaseError as e:
        exc = e
    except telethon.errors.MessageIdInvalidError as error:
        exc = MessageIdInvalidError(
            chat_id=chat_id,
            event_id=event_id,
            operation=NEW,
            error=error,
            messages=source_messages,
        )
    except telethon.errors.ChatForwardsRestrictedError:
        exc = MessageForwardsRestrictedError(
            chat_id=chat_id,
            event_id=event_id,
            operation=NEW,
        )
        if source and not source.is_rewrite:
            await send_error_to_admins(
                f"⚠ Источник {source_messages[0].chat.title} запрещает пересылку"
                " сообщений. Установите режим перепечатывания сообщений."
            )
    except (
        telethon.errors.MediaCaptionTooLongError,
        telethon.errors.MessageTooLongError,
    ) as error:
        exc = MessageTooLongError(
            chat_id=chat_id,
            event_id=event_id,
            operation=NEW,
            error=error,
            messages=source_messages,
        )
    except telethon.errors.BadRequestError as error:
        exc = MessageBadRequestError(
            chat_id=chat_id,
            event_id=event_id,
            operation=NEW,
            error=error,
            messages=source_messages,
        )
    except Exception as error:
        exc = MessageUnknownError(
            chat_id=chat_id,
            event_id=event_id,
            operation=NEW,
            error=error,
            messages=source_messages,
        )
    else:
        await user_client.send_read_acknowledge(
            entity=chat_id,
            message=source_messages,
        )
    finally:
        if blocked:
            blocked.remove(value=event_id)

        if exc and (history_obj := history.get(min(msg.id for msg in source_messages))):
            history_obj.data["first_message"]["exception"] = exc.to_dict()

        for history_obj in history.values():
            history_obj.save()


def get_repeated_history_id_or_none(chat_id: int, message_id: int) -> int | None:
    """Получить id из истории сообщения."""
    mh: type[MessageHistory] = MessageHistory.alias()
    try:
        history_obj = (
            mh.select(mh.id)
            .where(
                (
                    ((mh.source_id == chat_id) & (mh.source_message_id == message_id))
                    | (
                        (mh.source_forward_from_chat_id == chat_id)
                        & (mh.source_forward_from_message_id == message_id)
                    )
                    # В том числе как уже пересланное из другого источника
                )
                & (
                    mh.category_message_id != None  # noqa: E711
                )  # Отсутствующие сообщения в категории не учитываем
            )
            .get()
        )  # Работает по индексам

    except DoesNotExist:
        return  # noqa: R502

    return history_obj.id


async def new_one_message(
    message: patched.Message,
    source: Source,
    disable_notification: bool = False,
) -> patched.Message:
    """
    :return: Новое сообщение в категории, которой принадлежит источник.
    """
    if not source.is_rewrite:
        return await message.forward(
            chat_id=source.category.id,
            disable_notification=disable_notification,
        )

    is_media = is_media_message_with_caption(operation=NEW, message=message)

    cleanup_message(message=message, source=source, is_media=is_media)

    if not (message.text or is_media):
        raise MessageCleanedFullyError(operation=NEW, message=message)

    add_header(source=source, message=message)
    cut_long_message(message=message)

    message.web_page = None  # disable_web_page_preview = True

    try:
        return await message.copy(
            chat_id=source.category.id,
            disable_notification=disable_notification,
            **get_reply_to(message),
        )
    except pyrogram_errors.BadRequest:
        # Если неверно сформированы quote_text/quote_entities
        return await message.copy(
            chat_id=source.category.id,
            disable_notification=disable_notification,
        )


def get_reply_to(message: patched.Message):
    if not (message.reply_to_message and message.reply_to_message.chat):
        return dict(
            reply_to_chat_id=None,
            reply_to_message_id=None,
            quote_text=None,
            quote_entities=None,
        )

    if message.reply_to_message.chat.id == message.chat.id:
        try:
            history_msg = MessageHistory.get(
                (MessageHistory.source_id == message.chat.id)
                & (MessageHistory.source_message_id == message.reply_to_message_id)
                & MessageHistory.category_message_id.is_null(False)
                & MessageHistory.deleted_at.is_null()
            )
        except DoesNotExist:
            pass
        else:
            return dict(
                reply_to_chat_id=history_msg.category_id,
                reply_to_message_id=history_msg.category_message_id,
                quote_text=message.quote_text,
                quote_entities=message.quote_entities,
            )

    return dict(
        reply_to_chat_id=message.reply_to_message.chat.id,
        reply_to_message_id=message.reply_to_message_id,
        quote_text=message.quote_text,
        quote_entities=message.quote_entities,
    )


async def new_media_group_messages(
    messages: list[patched.Message],
    source: Source,
    disable_notification: bool = False,
) -> list[patched.Message]:
    """
    :return: Список новых сообщений в категории, которой принадлежит источник.
    """
    if not source.is_rewrite:
        return await client.forward_messages(
            chat_id=source.category.id,
            from_chat_id=messages[0].chat.id,
            message_ids=[item.id for item in messages],
            disable_notification=disable_notification,
        )

    media_has_caption = False
    for msg in messages:
        if msg.caption:
            media_has_caption = True
            cleanup_message(message=msg, source=source, is_media=True)
            add_header(source=source, message=msg)
            cut_long_message(message=msg)

    if not media_has_caption:
        add_header(source=source, message=messages[0])

    return await SendMediaGroup.send_media_group(
        client,
        chat_id=source.category.id,
        media=[get_input_media(message=msg) for msg in messages],
        disable_notification=disable_notification,
    )


def is_media_message_with_caption(operation: Operation, message: patched.Message):
    """
    Сообщение является медиа с возможностью подписи.

    :raise MessageMediaWithoutCaptionError: Сообщение является медиа, но не может содержать подпись.
    """
    if message.text:
        return False

    if message.media in (
        MessageMediaType.VOICE,
        MessageMediaType.VIDEO,
        MessageMediaType.AUDIO,
        MessageMediaType.PHOTO,
        MessageMediaType.DOCUMENT,
    ):
        return True

    raise MessageMediaWithoutCaptionError(operation=operation, message=message)
