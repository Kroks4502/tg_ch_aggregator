import logging

from pyrogram import Client, filters
from pyrogram.types import Message

from models import Source
from plugins.user.sources_monitoring.new_message.common import (
    handle_errors_on_new_message,
    logging_on_startup,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.cleanup import cleanup_message
from plugins.user.utils.history import add_to_category_history
from plugins.user.utils.inspector import is_new_and_valid_post
from plugins.user.utils.rewriter import rewrite_message


@Client.on_message(
    custom_filters.monitored_channels & ~filters.media_group & ~filters.service,
)
@handle_errors_on_new_message
async def new_regular_message(
    client: Client,
    message: Message,
    *,
    is_resending: bool = None,
):
    logging_on_startup(message, is_resending)

    source = Source.get(tg_id=message.chat.id)

    if not is_new_and_valid_post(message, source):
        await client.read_chat_history(message.chat.id)
        return

    if source.is_rewrite:
        cleanup_message(message, source)
        rewrite_message(message)
        message.web_page = None  # disable_web_page_preview = True
        forwarded_message = await message.copy(
            source.category.tg_id,
            disable_notification=is_resending,
        )
    else:
        forwarded_message = await message.forward(
            source.category.tg_id,
            disable_notification=is_resending,
        )

    add_to_category_history(
        message, forwarded_message, source, rewritten=source.is_rewrite
    )

    await client.read_chat_history(message.chat.id)
    logging.info(
        'Источник %s отправил сообщение %s, is_resending %s, оно отправлено в категорию %s',
        message.chat.id,
        message.id,
        is_resending,
        source.category_id,
    )
