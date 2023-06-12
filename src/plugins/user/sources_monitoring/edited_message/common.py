import logging

from pyrogram.types import Message

from config import MESSAGES_EDIT_LIMIT_TD
from models import CategoryMessageHistory, FilterMessageHistory
from plugins.user.utils.blocking import blocking_editable_messages
from plugins.user.utils.chats_locks import MessagesLocks


def logging_on_startup(message: Message) -> None:
    logging.debug(
        'Источник %s изменил сообщение %s',
        message.chat.id,
        message.id,
    )


def is_out_edit_timeout(message: Message) -> bool:
    """Таймаут редактирования сообщения истёк."""
    timedelta = message.edit_date - message.date
    if timedelta > MESSAGES_EDIT_LIMIT_TD:
        logging.info(
            'Источник %s изменил сообщение %s спустя %s',
            message.chat.id,
            message.id,
            timedelta,
        )
        return True
    return False


def try_set_blocked(message: Message) -> MessagesLocks | None:
    """Установить блокировку на сообщение чата."""
    blocked = blocking_editable_messages.get(message.chat.id)
    if blocked.contains(message.media_group_id) or blocked.contains(message.id):
        logging.warning(
            'Источник %s изменил сообщение %s, но оно уже заблокировано',
            message.chat.id,
            message.id,
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
            'Источник %s изменил сообщение %s от %s, оно отсутствует в истории',
            message.chat.id,
            message.id,
            message.date,
        )
        filter_obj: FilterMessageHistory = FilterMessageHistory.get_or_none(
            source_chat_id=message.chat.id,
            source_message_id=message.id,
        )
        if not filter_obj:
            logging.warning(
                'Источник %s изменил сообщение %s от %s, оно отсутствует и в истории категории, и в истории фильтра.',
                message.chat.id,
                message.id,
                message.date,
            )
        return
    return history_obj


def set_edited_on_history(history_obj: CategoryMessageHistory) -> None:
    history_obj.source_message_edited = True
    history_obj.save()

    logging.info(
        'Источник %s изменил сообщение %s. Оно изменено в категории %s',
        history_obj.source_chat_id,
        history_obj.source_message_id,
        history_obj.category_id,
    )
