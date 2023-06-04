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
from plugins.user.sources_monitoring.new_message.regular_message import (
    new_regular_message,
)
from plugins.user.utils import custom_filters


@Client.on_edited_message(
    custom_filters.monitored_channels & ~filters.media_group,
)
async def edit_regular_message(client: Client, message: Message):
    logging_on_startup(message)

    if is_out_edit_timeout(message):
        return

    history_obj = get_history_obj(message)
    if not history_obj:
        return

    blocked = try_set_blocked(message)
    if not blocked:
        return

    await client.delete_messages(history_obj.category.tg_id, history_obj.message_id)

    set_deleted_on_history(history_obj)

    await send_message_to_category(client, message, history_obj)

    blocked.remove(message.media_group_id or message.id)


def set_deleted_on_history(
    history_obj: CategoryMessageHistory,
) -> None:
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
    await new_regular_message(
        client,
        message,
        is_resending=True,  # Удалить
        history_obj=history_obj,  # Замена is_resending для возможности редактирования поста
    )
