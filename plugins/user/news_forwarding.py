from pyrogram import Client, filters
from pyrogram.types import Message

from log import logger
from models import Source
from settings import AGGREGATOR_CHANNEL
from plugins.user import custom_filters
from plugins.user.helpers import (add_to_filter_history,
                                  add_to_category_history,
                                  get_message_link,
                                  perform_check_history, perform_filtering)

media_group_ids = {}  # chat_id: [media_group_id ...]


def is_new_and_valid_post(message: Message, source: Source) -> bool:
    if h_obj := perform_check_history(message, source):
        logger.info(
            f'Сообщение {message.id} из чата {message.chat.id} ({message.link}) '
            f'уже есть в канале категории {source.category} '
            f'({get_message_link(h_obj.category.tg_id, h_obj.message_id)})')
        return False

    if filter_id := perform_filtering(message, source):
        add_to_filter_history(message, filter_id, source)
        logger.info(
            f'Сообщение {message.id} из чата {message.chat.id} ({message.link}) '
            f'отфильтровано. ID фильтра: {filter_id}')
        return False

    return True


@Client.on_message(
    custom_filters.monitored_channels
    & ~filters.media_group
    & ~filters.service
)
async def new_post_without_media_group(client: Client, message: Message):
    source = Source.get(tg_id=message.chat.id)

    if not is_new_and_valid_post(message, source):
        return

    forwarded_message = await message.forward(source.category.tg_id)
    await client.read_chat_history(message.chat.id)
    add_to_category_history(message, forwarded_message, source)


@Client.on_message(
    custom_filters.monitored_channels
    & filters.media_group
    & ~filters.service
)
async def new_post_with_media_group(client: Client, message: Message):
    chat = media_group_ids.get(message.chat.id)
    if not chat:
        chat = media_group_ids[message.chat.id] = []
        if len(media_group_ids) > 3:
            media_group_ids.pop(list(media_group_ids.keys())[0])

    if message.media_group_id in chat:
        return
    chat.append(message.media_group_id)

    source = Source.get(tg_id=message.chat.id)
    media_group_messages = await message.get_media_group()
    for m in media_group_messages:
        if not is_new_and_valid_post(m, source):
            return

    forwarded_messages = await client.forward_messages(
        AGGREGATOR_CHANNEL, message.chat.id,
        [item.id for item in media_group_messages])
    await client.read_chat_history(message.chat.id)
    add_to_category_history(message, forwarded_messages[0], source)


@Client.on_message(
    custom_filters.monitored_channels
    & filters.service
)
async def service_messages(client: Client, message: Message):
    await client.read_chat_history(message.chat.id)
