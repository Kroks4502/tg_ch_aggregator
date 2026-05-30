import logging

from telethon import errors as telethon_errors

from models import MessageHistory, Source
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageFilteredError,
    MessageIdInvalidError,
    MessageNotFoundOnHistoryError,
    MessageNotModifiedError,
    MessageNotOnCategoryError,
    MessageNotRewrittenError,
    MessageTooLongError,
    MessageUnknownError,
)
from plugins.user.sources_monitoring.common import (
    add_header,
    cut_long_message,
    get_filter_id_or_none,
    is_monitored_filter,
    set_blocking,
)
from plugins.user.types import Operation
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.dump import dump_message
from plugins.user.utils.telethon_helpers import (
    edit_message_with_entities,
    msg_entities,
    msg_text,
    tl_message_to_dict,
    _get_album_input_media,
)

EDIT = Operation.EDIT

log = logging.getLogger(__name__)


# Alias для обратной совместимости с тестами
async def edited_message(client, message) -> None:
    """Wrapper: обработать изменённое сообщение (совместимость с тестами)."""
    await _handle_edited_message(client, message)


async def on_edited_message(event):
    """
    Telethon event handler для изменённых сообщений из источников.
    Регистрируется в main.py через client.add_event_handler.
    """
    if not await is_monitored_filter(event):
        return

    message = event.message
    client = event.client
    await _handle_edited_message(client, message)


async def _handle_edited_message(client, message) -> None:  # noqa: C901
    """Основная логика обработки изменённого сообщения."""
    log.debug("Источник %s изменил сообщение %s", message.chat_id, message.id)
    dump_message(message=message, operation=EDIT)

    blocked = None
    history_obj = None
    history_data = {}
    exc = None
    try:
        blocked = set_blocking(
            operation=EDIT,
            message=message,
            block_value=message.id,
        )

        history_obj = MessageHistory.get_or_none(
            source_id=message.chat_id,
            source_message_id=message.id,
        )

        if not history_obj:
            raise MessageNotFoundOnHistoryError(operation=EDIT, message=message)

        history_obj.edited_at = message.edit_date
        history_data["source"] = tl_message_to_dict(message)

        if not history_obj.category_message_id:
            raise MessageNotOnCategoryError(operation=EDIT, message=message)

        if not history_obj.category_message_rewritten:
            raise MessageNotRewrittenError(operation=EDIT, message=message)

        source = Source.get(message.chat_id)

        filter_id = get_filter_id_or_none(message=message, source_id=source.id)
        history_obj.filter_id = filter_id
        if filter_id:
            raise MessageFilteredError(operation=EDIT, message=message)

        is_media = message.media is not None

        if msg_text(message):
            cleanup_message(message=message, source=source)
            await add_header(client, source=source, message=message)
            cut_long_message(message=message)
        elif (
            not history_obj.category_media_group_id
            or not _is_text_in_mediagroup(history_obj)
        ):
            await add_header(client, source=source, message=message)

        if is_media:
            await edit_message_with_entities(
                client,
                chat_id=history_obj.category_id,
                msg_id=history_obj.category_message_id,
                text=msg_text(message) or "",
                entities=msg_entities(message) or [],
                media=_get_album_input_media(message),
            )
            # Получаем обновлённое сообщение для сохранения в history
            try:
                cat_messages = await client.get_messages(
                    history_obj.category_id,
                    ids=[history_obj.category_message_id],
                )
                category_message = cat_messages[0] if cat_messages else None
            except Exception:
                category_message = None
        else:
            # Редактируем текстовое сообщение через edit_message_with_entities
            await edit_message_with_entities(
                client,
                chat_id=history_obj.category_id,
                msg_id=history_obj.category_message_id,
                text=msg_text(message) or "",
                entities=msg_entities(message) or [],
            )
            category_message = None

        log.info(
            "Источник %s изменил сообщение %s → обновлено в категории %s",
            message.chat_id, message.id, source.category_id,
        )

        if category_message:
            history_data["category"] = tl_message_to_dict(category_message)

    except MessageBaseError as e:
        exc = e
    except telethon_errors.MessageNotModifiedError as error:
        exc = MessageNotModifiedError(operation=EDIT, message=message, error=error)
    except telethon_errors.MessageIdInvalidError as error:
        exc = MessageIdInvalidError(operation=EDIT, message=message, error=error)
    except telethon_errors.MessageTooLongError as error:
        exc = MessageTooLongError(operation=EDIT, message=message, error=error)
    except telethon_errors.BadRequestError as error:
        exc = MessageBadRequestError(operation=EDIT, message=message, error=error)
    except Exception as error:
        exc = MessageUnknownError(operation=EDIT, message=message, error=error)
    finally:
        if blocked:
            blocked.remove(value=message.id)

        if history_obj:
            if exc:
                history_data["exception"] = exc.to_dict()
                history_obj.data["last_message_with_error"] = history_data
            else:
                history_obj.data["last_message_without_error"] = history_data

            history_obj.save()


def _is_text_in_mediagroup(history_obj: MessageHistory) -> bool:
    """Есть ли текст хотя бы в одном сообщении медиа-группы (кроме текущего)."""
    mh = MessageHistory.alias()
    return (
        mh.select()
        .where(
            (mh.category_id == history_obj.category_id)
            & (mh.category_media_group_id == history_obj.category_media_group_id)
            & (mh.category_message_id != history_obj.category_message_id)
            & (
                (
                    mh.data.path("last_message_without_error", "category").is_null()
                    & mh.data.path("first_message", "category", "text").is_null(False)
                )
                | (
                    mh.data.path(
                        "last_message_without_error", "category", "text"
                    ).is_null(False)
                )
            )
        )
        .exists()
    )
