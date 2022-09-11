from pyrogram import Client, filters
from pyrogram.types import Message

from initialization import logger, user
from models import Source


@Client.on_message(
    filters.private
    & filters.reply
    & filters.command(['sent_from', 'send_to'])
)
async def bot_meta_for_new_task(client: Client, meta_message: Message):
    try:
        channel_id = int(meta_message.command[-1])
    except ValueError:
        logger.error('Мета-сообщение %s некорректно: %s',
                     meta_message.id, meta_message.text)
        return

    if meta_message.command[0] == 'sent_from':
        channel = Source.get(tg_id=channel_id)
        if not channel:
            logger.error('Источника сообщения нет в базе данных %s',
                         meta_message.id)
            return

        is_unique, msg = await is_unique_message(channel.category,
                                                 meta_message.reply_to_message)
        if not is_unique:
            await meta_message.reply_to_message.reply(msg, quote=True)
            return
        channel_id = channel.category.tg_id

    message = meta_message.reply_to_message
    if message.media_group_id:
        messages_id_media_group = [
            item.id
            for item in await message.get_media_group()
        ]
        return await client.forward_messages(
            channel_id,
            message.chat.id,
            messages_id_media_group)
    return await message.forward(channel_id)


async def is_unique_message(category, new_message):
    # todo добиться получения истории ботом
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
            msg = f'Сообщение {new_message.id} уже есть в канале {category.title} #повтор'
            logger.debug(msg)
            return False, msg
    return True, ''
