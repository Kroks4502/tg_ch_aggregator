import json
import logging

from peewee import DoesNotExist
from pyrogram import Client
from pyrogram import errors as pyrogram_errors
from pyrogram import filters
from pyrogram.enums import MessageMediaType
from pyrogram.types import Message

from models import MessageHistory, Source
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageCleanedFullyError,
    MessageFilteredError,
    MessageForwardsRestrictedError,
    MessageIdInvalidError,
    MessageMediaWithoutCaptionError,
    MessageRepeatedError,
    MessageTooLongError,
    Operation,
)
from plugins.user.sources_monitoring.common import (
    add_header,
    cut_long_message,
    get_filter_id_or_none,
    get_input_media,
    set_blocking,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.senders import send_error_to_admins
from pyrogram_fork.send_media_group import SendMediaGroup

NEW = Operation.NEW


@Client.on_message(
    custom_filters.monitored_channels & ~filters.service,
)
async def new_message(client: Client, message: Message):  # noqa: C901
    logging.debug(
        'Источник %s отправил сообщение %s',
        message.chat.id,
        message.id,
    )

    blocked = None
    source_messages = None
    history = dict()
    exc = None
    try:
        blocked = set_blocking(
            operation=NEW,
            message=message,
            block_value=message.media_group_id or message.id,
        )

        if message.media_group_id:
            source_messages = await message.get_media_group()  # Первый await !
        else:
            source_messages = [message]

        source = Source.get(message.chat.id)

        repeated = False
        filtered = False
        for msg in source_messages:
            repeat_history_id = get_repeated_history_id_or_none(
                message=msg, category_id=source.category_id
            )
            repeated = True if repeat_history_id else repeated

            filter_id = get_filter_id_or_none(message=msg, source_id=source.id)
            filtered = True if filter_id else filtered

            history[msg.id] = MessageHistory(
                source_id=source.id,
                source_message_id=msg.id,
                source_media_group_id=msg.media_group_id,
                source_forward_from_chat_id=msg.forward_from_chat.id
                if msg.forward_from_message_id
                else None,
                source_forward_from_message_id=msg.forward_from_message_id,
                category_id=source.category_id,
                repeat_history_id=repeat_history_id,
                filter_id=filter_id,
                created_at=msg.date,
                data=[dict(source=json.loads(msg.__str__()))],
            )

        if repeated:
            raise MessageRepeatedError(operation=NEW, message=message)

        if filtered:
            raise MessageFilteredError(operation=NEW, message=message)

        if not message.media_group_id:
            category_messages = [
                await new_one_message(
                    message=message,
                    source=source,
                )
            ]

            logging.info(
                'Источник %s отправил сообщение %s, оно отправлено в категорию %s',
                message.chat.id,
                message.id,
                source.category_id,
            )
        else:  # Медиа группа
            category_messages = await new_media_group_messages(
                client=client,
                messages=source_messages,
                source=source,
            )

            logging.info(
                'Источник %s отправил сообщение %s в составе медиа группы %s, '
                'сообщения отправлены в категорию %s',
                message.chat.id,
                message.id,
                message.media_group_id,
                source.category_id,
            )

        for src_msg, cat_msg in zip(source_messages, category_messages):
            history_obj = history[src_msg.id]
            history_obj.category_message_rewritten = source.is_rewrite
            history_obj.category_message_id = cat_msg.id
            history_obj.category_media_group_id = cat_msg.media_group_id
            history_obj.data[-1]['category'] = json.loads(cat_msg.__str__())

    except MessageBaseError as e:
        exc = e
    except pyrogram_errors.MessageIdInvalid as error:
        exc = MessageIdInvalidError(operation=NEW, message=message, error=error)
    except pyrogram_errors.ChatForwardsRestricted:
        exc = MessageForwardsRestrictedError(operation=NEW, message=message)
        await send_error_to_admins(
            f'⚠ Источник {message.chat.title} запрещает пересылку сообщений. '
            'Установите режим перепечатывания сообщений.'
        )
    except (
        pyrogram_errors.MediaCaptionTooLong,
        pyrogram_errors.MessageTooLong,
    ) as error:
        exc = MessageTooLongError(operation=NEW, message=message, error=error)
    except pyrogram_errors.BadRequest as error:
        exc = MessageBadRequestError(operation=NEW, message=message, error=error)
    finally:
        if blocked:
            blocked.remove(value=message.media_group_id or message.id)

        if exc and (history_obj := history.get(message.id)):
            history_obj.data[-1]['exception'] = exc.to_dict()

        for history_obj in history.values():
            history_obj.save()

        if source_messages:
            await client.read_chat_history(
                chat_id=message.chat.id,
                max_id=max(msg.id for msg in source_messages),
            )


def get_repeated_history_id_or_none(message: Message, category_id: int) -> int | None:
    """Получить id из истории сообщения."""
    if message.forward_from_chat:  # Сообщение переслано в источник из другого чата
        # Сообщение уже может быть в истории по этому чату, если он является источником
        source_chat_id = message.forward_from_chat.id
        source_message_id = message.forward_from_message_id

        # Проверяем не пересылалось ли уже в других источниках это сообщение
        forward_from_chat_id = message.forward_from_chat.id
        forward_from_message_id = message.forward_from_message_id
    else:  # Сообщение не является пересланным
        # Проверяем наличие этого сообщения в истории
        source_chat_id = message.chat.id
        source_message_id = message.id

        # Проверяем не получили ли мы это сообщение ранее как пересланное из другого источника
        forward_from_chat_id = message.chat.id
        forward_from_message_id = message.id

    mh: type[MessageHistory] = MessageHistory.alias()
    try:
        history_obj = (
            mh.select(mh.id)
            .where(
                (mh.category_id == category_id)
                # Все проверки выполняем в рамках одной категории
                & (
                    (
                        (mh.source_id == source_chat_id)
                        & (mh.source_message_id == source_message_id)
                    )
                    | (
                        (mh.source_forward_from_chat_id == forward_from_chat_id)
                        & (mh.source_forward_from_message_id == forward_from_message_id)
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
    message: Message,
    source: Source,
    disable_notification: bool = False,
) -> Message:
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

    add_header(message=message)
    cut_long_message(message=message)

    message.web_page = None  # disable_web_page_preview = True
    return await message.copy(
        chat_id=source.category.id,
        disable_notification=disable_notification,
    )


async def new_media_group_messages(
    client: Client,
    messages: list[Message],
    source: Source,
    disable_notification: bool = False,
) -> list[Message]:
    """
    :return: Список новых сообщений в категории, которой принадлежит источник.
    """
    if not source.is_rewrite:
        return await client.forward_messages(
            chat_id=source.category.tg_id,
            from_chat_id=messages[0].chat.id,
            message_ids=[item.id for item in messages],
            disable_notification=disable_notification,
        )

    media_has_caption = False
    for msg in messages:
        if msg.caption:
            media_has_caption = True
            cleanup_message(message=msg, source=source, is_media=True)
            add_header(message=msg)
            cut_long_message(message=msg)

    if not media_has_caption:
        add_header(message=messages[0])

    return await SendMediaGroup.send_media_group(
        client,
        chat_id=source.category.id,
        media=[get_input_media(message=msg) for msg in messages],
        disable_notification=disable_notification,
    )


def is_media_message_with_caption(operation: Operation, message: Message):
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
