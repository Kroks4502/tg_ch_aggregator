from pyrogram import Client, filters
from pyrogram.types import Message

from initialization import AGGREGATOR_CHANNEL
from plugins.user import custom_filters


@Client.on_message(
    ~filters.media_group
    & ~filters.poll
    & ~filters.service
    & custom_filters.monitored_channels
)
async def new_post_without_media_group(client: Client, message: Message):
    forwarded_message = await message.forward(AGGREGATOR_CHANNEL)

    is_promo_message, promo_comment = await custom_filters.is_promo_message(None, None, message)
    reply_text = f'Источник: [{message.chat.title}]({message.link})\n'
    if not is_promo_message:
        reply_text = f'/sent_from {message.chat.id}\n' + reply_text
    else:
        reply_text += f'{promo_comment} #отфильтровано'

    await forwarded_message.reply(reply_text, disable_web_page_preview=True)
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

        is_promo_message = False
        promo_comment = ''
        for item in messages_id_media_group:
            is_promo_message, promo_comment = await custom_filters.is_promo_message(
                None, None, item)
            if is_promo_message:
                break

        messages_id_media_group = [item.id
                                   for item in messages_id_media_group]
        forwarded_messages = await client.forward_messages(
            AGGREGATOR_CHANNEL, message.chat.id, messages_id_media_group)

        reply_text = f'Источник: [{message.chat.title}]({message.link})\n'
        if not is_promo_message:
            reply_text = f'/sent_from {message.chat.id}\n' + reply_text
        else:
            reply_text += f'{promo_comment} #отфильтровано'

        await forwarded_messages[-1].reply(reply_text,
                                           disable_web_page_preview=True)
        await client.read_chat_history(
            message.chat.id, max(messages_id_media_group))
