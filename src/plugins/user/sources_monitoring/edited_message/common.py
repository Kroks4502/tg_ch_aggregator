import logging

from pyrogram.types import Message

from common import get_shortened_text
from config import MESSAGES_EDIT_LIMIT_TD
from models import CategoryMessageHistory, FilterMessageHistory
from plugins.user.utils.blocking import blocking_editable_messages
from plugins.user.utils.chats_locks import MessagesLocks


def logging_on_startup(message: Message) -> None:
    logging.debug(
        f'Источник {get_shortened_text(message.chat.title, 20)} {message.chat.id} '
        f'изменил сообщение {message.id}'
    )


def is_out_edit_timeout(message: Message) -> bool:
    """Таймаут редактирования сообщения истёк."""
    if message.edit_date - message.date > MESSAGES_EDIT_LIMIT_TD:
        logging.info(
            f'Сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} изменено'
            f' спустя {(message.edit_date - message.date).seconds // 60} мин.'
        )
        return True
    return False


def try_set_blocked(message: Message) -> MessagesLocks | None:
    """Установить блокировку на сообщение чата."""
    blocked = blocking_editable_messages.get(message.chat.id)
    if blocked.contains(message.media_group_id) or blocked.contains(message.id):
        logging.warning(
            f'Изменение сообщения {message.id} '
            'из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} заблокировано.'
        )
        return
    blocked.add(message.media_group_id or message.id)
    return blocked


def get_history_obj(
    message: Message,
) -> CategoryMessageHistory | None:
    """Получить объект из истории сообщений категории."""
    history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
        source_chat_id=message.chat.id,
        source_message_id=message.id,
        deleted=False,
    )
    if not history_obj:
        logging.info(
            f'Измененное сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} от'
            f' {message.date} отсутствует в истории категории.'
        )
        filter_obj: FilterMessageHistory = FilterMessageHistory.get_or_none(
            source_chat_id=message.chat.id,
            source_message_id=message.id,
        )
        if not filter_obj:
            logging.warning(
                f'Измененное сообщение {message.id} из источника'
                f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} от'
                f' {message.date} отсутствует и в истории категории, и в истории фильтра.'
            )
        return
    return history_obj
