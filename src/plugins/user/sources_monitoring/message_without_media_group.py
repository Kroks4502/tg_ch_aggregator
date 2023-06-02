import logging
import re

from pyrogram import Client, filters
from pyrogram.errors import BadRequest, MessageIdInvalid
from pyrogram.types import Message

from common import get_shortened_text
from config import PATTERN_AGENT
from models import Source
from plugins.user.utils import custom_filters
from plugins.user.utils.history import add_to_category_history
from plugins.user.utils.inspector import is_new_and_valid_post
from plugins.user.utils.rewriter import delete_agent_text_in_message


@Client.on_message(
    custom_filters.monitored_channels & ~filters.media_group & ~filters.service,
)
async def message_without_media_group(
    client: Client,
    message: Message,
    *,
    is_resending: bool = None,
):
    if not is_resending:
        logging.debug(
            f'Источник {get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'отправил сообщение {message.id}'
        )
    else:
        logging.debug(
            'Повторная отправка из источника '
            f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'сообщения {message.id}'
        )

    source = Source.get(tg_id=message.chat.id)

    if not is_new_and_valid_post(message, source):
        await client.read_chat_history(message.chat.id)
        return

    message_text = message.text or message.caption or ''
    search_result = re.search(PATTERN_AGENT, str(message_text))
    try:
        if search_result:
            delete_agent_text_in_message(search_result, message)
            message.web_page = None  # disable_web_page_preview = True
            forwarded_message = await message.copy(
                source.category.tg_id, disable_notification=is_resending
            )
        else:
            forwarded_message = await message.forward(
                source.category.tg_id, disable_notification=is_resending
            )

        add_to_category_history(
            message, forwarded_message, source, rewritten=bool(search_result)
        )

        await client.read_chat_history(message.chat.id)
        logging.info(
            f'Сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} переслано'
            ' в категорию'
            f' {get_shortened_text(source.category.title, 20)} {source.category.tg_id}'
        )
    except MessageIdInvalid as e:
        # Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника.
        logging.warning(
            f'Сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} привело к'
            f' ошибке {e}'
        )
    except BadRequest as e:
        logging.error(
            (
                f'Сообщение {message.id} из источника'
                f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} привело'
                f' к ошибке.\n{e}\nПолное сообщение: {message}\n'
            ),
            exc_info=True,
        )
