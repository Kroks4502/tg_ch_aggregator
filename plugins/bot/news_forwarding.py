from pyrogram import Client, filters
from pyrogram.types import Message

from initialization import logger, user, AGGREGATOR_CHANNEL
from models import Source
from plugins.bot.menu import custom_filters


# @Client.on_message(
#     filters.private
#     & filters.reply
#     & filters.command(['sent_from', 'send_to'])
# )
# async def bot_meta_for_new_task(client: Client, meta_message: Message):
#     try:
#         channel_id = int(meta_message.command[-1])
#     except ValueError:
#         logger.error('Мета-сообщение %s некорректно: %s',
#                      meta_message.id, meta_message.text)
#         return
#
#     if meta_message.command[0] == 'sent_from':
#         channel = Source.get(tg_id=channel_id)
#         if not channel:
#             logger.error('Источника сообщения нет в базе данных %s',
#                          meta_message.id)
#             return
#
#         is_unique, msg = await is_unique_message(channel.category,
#                                                  meta_message.reply_to_message)
#         if not is_unique:
#             await meta_message.reply_to_message.reply(msg, quote=True)
#             return
#         channel_id = channel.category.tg_id
#
#     message = meta_message.reply_to_message
#     if message.media_group_id:
#         messages_id_media_group = [
#             item.id
#             for item in await message.get_media_group()
#         ]
#         return await client.forward_messages(
#             channel_id,
#             message.chat.id,
#             messages_id_media_group)
#     return await message.forward(channel_id)
#

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
