from pyrogram.types import Message

from models import Source
from plugins.user.exceptions import (
    MessageBlockedByIdError,
    MessageBlockedByMediaGroupError,
    Operation,
)
from plugins.user.utils.chats_locks import ChatsLocks, MessagesLocks
from plugins.user.utils.inspector import FilterInspector

blocking_messages = ChatsLocks('all')


def set_blocking(
    operation: Operation, message: Message, block_value: int
) -> MessagesLocks:
    """
    Установить блокировку для сущности.

    :param operation: Производимая операция (для исключения).
    :param message: Сообщение источника (для исключения).
    :param block_value: ID для блокировки (message.id или message.media_group_id).
    :raise MessageBlockedByMediaGroupError: Сообщение заблокировано в составе медиагруппы.
    :raise MessageBlockedByIdError: Сообщение заблокировано по ID
    :return:
    """
    blocked = blocking_messages.get(key=message.chat.id)
    if blocked.contains(key=message.media_group_id):
        raise MessageBlockedByMediaGroupError(
            operation=operation, message=message, blocked=blocked
        )
    if blocked.contains(key=message.id):
        raise MessageBlockedByIdError(
            operation=operation, message=message, blocked=blocked
        )
    blocked.add(value=block_value)
    return blocked


def get_filter_id_or_none(message: Message, source: Source) -> int | None:
    """Получить ID фильтра, который не прошёл текст сообщения."""
    if data := check_message_filter(message, source):
        return data['id']

    return  # noqa R502


def check_message_filter(message: Message, source: Source) -> dict | None:
    """Получить информацию о прохождении фильтра, если сообщение его не проходит."""

    inspector = FilterInspector(message, source)

    if result := inspector.check_message_type():
        return result

    if message.text or message.caption:
        if result := inspector.check_white_text():
            return result
        if result := inspector.check_text():
            return result

    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if result := inspector.check_entities(entity):
                return result

    return  # noqa R502
