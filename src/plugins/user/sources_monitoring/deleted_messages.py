import datetime as dt
import logging
import types as builtin_types

from telethon import errors as telethon_errors
from telethon.events import MessageDeleted

from models import MessageHistory
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageNotFoundOnHistoryError,
    MessageNotOnCategoryError,
    MessageUnknownError,
)
from plugins.user.sources_monitoring.common import _get_active_source_ids
from plugins.user.types import Operation
from plugins.user.utils.dump import dump_message

DELETE = Operation.DELETE

log = logging.getLogger(__name__)


async def on_deleted_messages(event: MessageDeleted.Event):
    """
    Telethon event handler для удалённых сообщений.

    Телеграм не отдаёт содержимое удалённых сообщений — только IDs.
    Поэтому в event.deleted_ids находятся только message_id.
    event.chat_id может быть None если канал неизвестен userbot'у.
    """
    if not event.chat_id:
        return

    source_ids = await _get_active_source_ids()
    if event.chat_id not in source_ids:
        return

    client = event.client
    for msg_id in event.deleted_ids:
        await _handle_deleted_message(client, event.chat_id, msg_id)


async def _handle_deleted_message(client, chat_id: int, msg_id: int) -> None:
    """Обработать одно удалённое сообщение."""
    log.debug("Источник %s удалил сообщение %s", chat_id, msg_id)

    # Создаём минимальный объект сообщения для dump и исключений
    minimal_msg = builtin_types.SimpleNamespace(
        chat_id=chat_id,
        id=msg_id,
        date=None,
        edit_date=None,
        grouped_id=None,
        media=None,
        text=None,
    )
    dump_message(message=minimal_msg, operation=DELETE)

    history_obj: MessageHistory = MessageHistory.get_or_none(
        source_id=chat_id,
        source_message_id=msg_id,
    )

    exc = None
    history_data = {}
    try:
        if not history_obj:
            raise MessageNotFoundOnHistoryError(operation=DELETE, message=minimal_msg)

        history_obj.deleted_at = dt.datetime.now()
        history_data = dict(source={"id": msg_id, "chat_id": chat_id})

        if not history_obj.category_message_id:
            raise MessageNotOnCategoryError(operation=DELETE, message=minimal_msg)

        await client.delete_messages(
            entity=history_obj.category.id,
            message_ids=history_obj.category_message_id,
        )

        history_obj.category_message_id = None

        log.info(
            "Источник %s удалил сообщение %s → удалено из категории",
            chat_id,
            msg_id,
        )
    except MessageBaseError as e:
        exc = e
    except telethon_errors.BadRequestError as error:
        exc = MessageBadRequestError(operation=DELETE, message=minimal_msg, error=error)
    except Exception as error:
        exc = MessageUnknownError(operation=DELETE, message=minimal_msg, error=error)
    finally:
        if history_obj:
            if exc:
                history_data["exception"] = exc.to_dict()
                history_obj.data["last_message_with_error"] = history_data
            else:
                history_obj.data["last_message_without_error"] = history_data

            history_obj.save()
