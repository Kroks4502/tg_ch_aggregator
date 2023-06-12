import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from models import CategoryMessageHistory, Source
from plugins.user.sources_monitoring.edited_message.common import (
    get_history_obj,
    is_out_edit_timeout,
    logging_on_startup,
    set_edited_on_history,
    try_set_blocked,
)
from plugins.user.sources_monitoring.new_message.regular_message import (
    new_regular_message,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.rewriter import rewrite_message


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

    if history_obj.rewritten:
        source = Source.get(tg_id=message.chat.id)
        cleanup_message(message, source)
        rewrite_message(message)
        if message.media:
            await client.edit_message_caption(
                chat_id=history_obj.category.tg_id,
                message_id=history_obj.message_id,
                caption=message.caption,
                caption_entities=message.caption_entities,
            )
        else:
            await client.edit_message_text(
                chat_id=history_obj.category.tg_id,
                message_id=history_obj.message_id,
                text=message.text,
                entities=message.entities,
                disable_web_page_preview=True,
            )
        set_edited_on_history(history_obj)
    else:
        await client.delete_messages(history_obj.category.tg_id, history_obj.message_id)
        set_deleted_on_history(history_obj)
        await send_message_to_category(client, message)

    blocked.remove(message.media_group_id or message.id)


def set_deleted_on_history(history_obj: CategoryMessageHistory) -> None:
    history_obj.source_message_edited = True
    history_obj.deleted = True
    history_obj.save()

    logging.info(
        'Источник %s изменил сообщение %s. Оно удалено из категории %s',
        history_obj.source_chat_id,
        history_obj.source_message_id,
        history_obj.category_id,
    )


async def send_message_to_category(
    client: Client,
    message: Message,
) -> None:
    await new_regular_message(
        client,
        message,
        is_resending=True,
    )
