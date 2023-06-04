import logging

from pyrogram import Client
from pyrogram.types import Message

from common import get_shortened_text
from config import MESSAGES_EDIT_LIMIT_TD
from models import CategoryMessageHistory, FilterMessageHistory
from plugins.user.sources_monitoring.blocking import (
    blocking_editable_messages,
    blocking_received_media_groups,
)
from plugins.user.sources_monitoring.message_with_media_group import (
    message_with_media_group,
)
from plugins.user.sources_monitoring.message_without_media_group import (
    message_without_media_group,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.chats_locks import MessagesLocks


@Client.on_edited_message(
    custom_filters.monitored_channels,
)
async def edited_message(client: Client, message: Message):
    logging_on_startup(message)

    if is_out_edit_timeout(message):
        return

    history_obj = get_history_obj(message)
    if not history_obj:
        return

    blocked = try_set_blocked(message)
    if not blocked:
        return

    messages_to_delete = get_message_to_delete(history_obj)

    if messages_to_delete:
        await client.delete_messages(history_obj.category.tg_id, messages_to_delete)

        set_deleted_on_history(history_obj, messages_to_delete)

        await send_message_to_category(client, message, history_obj)

    blocked.remove(message.media_group_id or message.id)


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


def get_message_to_delete(history_obj: CategoryMessageHistory) -> list[int]:
    if history_obj.media_group:
        query = CategoryMessageHistory.select().where(
            (CategoryMessageHistory.source == history_obj.source)
            & (CategoryMessageHistory.media_group == history_obj.media_group)
            & (CategoryMessageHistory.deleted == False)
        )
        return [m.message_id for m in query]

    return [history_obj.message_id]


def set_deleted_on_history(
    history_obj: CategoryMessageHistory,
    messages_to_delete: list[int],
) -> None:
    if history_obj.media_group:
        cmh = CategoryMessageHistory.alias()
        query = cmh.update(
            {
                cmh.source_message_edited: True,
                cmh.deleted: True,
            }
        ).where(
            (cmh.category == history_obj.category)
            & (cmh.message_id << messages_to_delete)
        )
        query.execute()
        logging.info(
            f'Сообщение {history_obj.source_message_id} из источника'
            f' {get_shortened_text(history_obj.source.title, 20)} {history_obj.source.tg_id} было'
            ' изменено. Все сообщения медиа-группы были удалены.'
            f' {get_shortened_text(history_obj.category.title, 20)} {history_obj.category.tg_id}'
        )
    else:
        history_obj.source_message_edited = True
        history_obj.deleted = True
        history_obj.save()
        logging.info(
            f'Сообщение {history_obj.source_message_id} из источника'
            f' {get_shortened_text(history_obj.source.title, 20)} {history_obj.source.tg_id} было'
            ' изменено. Оно удалено из категории'
            f' {get_shortened_text(history_obj.category.title, 20)} {history_obj.category.tg_id}'
        )


async def send_message_to_category(
    client: Client,
    message: Message,
    history_obj: CategoryMessageHistory,
) -> None:
    if message.media_group_id:
        if b := blocking_received_media_groups.get(message.chat.id):
            b.remove(message.media_group_id)
        await message_with_media_group(
            client,
            message,
            is_resending=True,  # Удалить
            history_obj=history_obj,  # Замена is_resending для возможности редактирования поста
        )
    else:
        await message_without_media_group(
            client,
            message,
            is_resending=True,  # Удалить
            history_obj=history_obj,  # Замена is_resending для возможности редактирования поста
        )
