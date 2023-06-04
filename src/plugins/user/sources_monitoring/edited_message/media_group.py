import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from common import get_shortened_text
from models import CategoryMessageHistory
from plugins.user.sources_monitoring.edited_message.common import (
    get_history_obj,
    is_out_edit_timeout,
    logging_on_startup,
    try_set_blocked,
)
from plugins.user.sources_monitoring.new_message.media_group import (
    new_media_group_message,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.blocking import blocking_received_media_groups


@Client.on_edited_message(
    custom_filters.monitored_channels & filters.media_group,
)
async def edited_media_group_message(client: Client, message: Message):
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

    await client.delete_messages(history_obj.category.tg_id, messages_to_delete)

    set_deleted_on_history(history_obj, messages_to_delete)

    await send_message_to_category(client, message)

    blocked.remove(message.media_group_id or message.id)


def get_message_to_delete(history_obj: CategoryMessageHistory) -> list[int]:
    query = CategoryMessageHistory.select().where(
        (CategoryMessageHistory.source == history_obj.source)
        & (CategoryMessageHistory.media_group == history_obj.media_group)
        & (CategoryMessageHistory.deleted == False)
    )
    return [m.message_id for m in query]


def set_deleted_on_history(
    history_obj: CategoryMessageHistory,
    messages_to_delete: list[int],
) -> None:
    query = CategoryMessageHistory.update(
        {
            CategoryMessageHistory.source_message_edited: True,
            CategoryMessageHistory.deleted: True,
        }
    ).where(
        (CategoryMessageHistory.category == history_obj.category)
        & (CategoryMessageHistory.message_id << messages_to_delete)
    )
    query.execute()
    logging.info(
        f'Сообщение {history_obj.source_message_id} из источника'
        f' {get_shortened_text(history_obj.source.title, 20)} {history_obj.source.tg_id} было'
        ' изменено. Все сообщения медиа-группы были удалены.'
        f' {get_shortened_text(history_obj.category.title, 20)} {history_obj.category.tg_id}'
    )


async def send_message_to_category(
    client: Client,
    message: Message,
    # history_obj: CategoryMessageHistory,
) -> None:
    if b := blocking_received_media_groups.get(message.chat.id):
        b.remove(message.media_group_id)
    await new_media_group_message(
        client,
        message,
        is_resending=True,  # Удалить
        # history_obj=history_obj,  # Замена is_resending для возможности редактирования поста
    )
