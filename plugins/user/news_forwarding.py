from pyrogram import Client, filters
from pyrogram.types import Message

from initialization import PROMO_CHANNEL, BOT_CHAT_ID
from plugins.user import custom_filters


@Client.on_message(
    ~filters.media_group
    & ~filters.poll
    & ~filters.service
    & custom_filters.monitored_channels
)
async def new_post_without_media_group(client: Client, message: Message):
    command = 'sent_from'
    source_id = message.chat.id

    is_promo_massage, msg = await custom_filters.is_promo_message(None, None, message)
    if is_promo_massage:
        command = 'send_to'
        source_id = PROMO_CHANNEL

    new_message = await message.forward(BOT_CHAT_ID)
    await new_message.reply(f'/{command} {source_id}')
    if msg:
        await new_message.reply(f'{msg} #промо')
    await client.read_chat_history(message.chat.id, message.id)


media_group_ids = {}


@Client.on_message(
    filters.media_group
    & custom_filters.monitored_channels
)
async def new_post_with_media_group(client: Client, message: Message):
    chat = media_group_ids.get(message.chat.id)
    if not chat:
        chat = media_group_ids[message.chat.id] = []

    if message.media_group_id not in chat:
        chat.append(message.media_group_id)

        messages_id_media_group = await message.get_media_group()

        command = 'sent_from'
        source_id = message.chat.id
        msg = ''
        for item in messages_id_media_group:
            is_promo_message, msg = await custom_filters.is_promo_message(
                None, None, item)
            if is_promo_message:
                command = 'send_to'
                source_id = PROMO_CHANNEL
                break

        messages_id_media_group = [item.id
                                   for item in messages_id_media_group]
        sent_messages = await client.forward_messages(
            BOT_CHAT_ID, message.chat.id, messages_id_media_group)
        await sent_messages[-1].reply(f'/{command} {source_id}')
        if msg:
            await sent_messages[-1].reply(f'{msg} #промо')
        await client.read_chat_history(
            message.chat.id, max(messages_id_media_group))
