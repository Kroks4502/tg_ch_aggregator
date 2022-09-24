from pyrogram import Client, filters
from pyrogram.types import Message

from log import logger
from settings import AGGREGATOR_CHANNEL
from initialization import user
from models import Source
from plugins.bot.menu import custom_filters


async def is_unique_message(category, new_message):
    # todo прекратить массово запрашивать историю - хранить локально?
    async for h_message in user.get_chat_history(category.tg_id, 30):
        if (
                h_message.forward_from_chat
                and new_message.forward_from_chat
                and h_message.forward_from_chat.id
                == new_message.forward_from_chat.id
                and h_message.forward_from_message_id
                == new_message.forward_from_message_id
        ):
            msg = (f'Сообщение {new_message.id} уже есть в канале '
                   f'[{category.title}]({h_message.link}) #повтор')
            logger.debug(msg)
            return False, msg
    return True, ''


@Client.on_message(
    custom_filters.chat(AGGREGATOR_CHANNEL)
    & filters.reply
    & filters.command(['sent_from', ], ['/', '\n'])
)
async def new_task(client: Client, meta_message: Message):
    try:
        source_channel_id = int(meta_message.command[1])
    except ValueError:
        err = (f'Мета-сообщение {meta_message.id} ' 
               f'некорректно: {meta_message.text}')
        logger.error(err)
        await meta_message.reply(err, quote=True)
        return

    source = Source.get(tg_id=source_channel_id)
    if not source:
        err = f'Источника сообщения нет в базе данных {meta_message.id}'
        logger.warning(err)
        await meta_message.reply(err, quote=True)
        return

    is_unique, msg = await is_unique_message(source.category,
                                             meta_message.reply_to_message)
    if not is_unique:
        await meta_message.reply_to_message.reply(msg, quote=True)
        return

    message = meta_message.reply_to_message
    if message.media_group_id:
        messages_id_media_group = [
            item.id
            for item in await message.get_media_group()
        ]
        return await client.forward_messages(
            source.category.tg_id,
            message.chat.id,
            messages_id_media_group)
    return await message.forward(source.category.tg_id)
