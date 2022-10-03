from pyrogram import Client, filters
from pyrogram.types import Message

from plugins.user.helpers import save_history
from settings import AGGREGATOR_CHANNEL
from plugins.user import custom_filters
from plugins.user.checks import is_passed_filter


@Client.on_message(
    ~filters.media_group
    & ~filters.poll
    & ~filters.service
    & custom_filters.monitored_channels
)
async def new_post_without_media_group(client: Client, message: Message):
    forwarded_message = await message.forward(AGGREGATOR_CHANNEL)

    is_pf, filter_comment = await is_passed_filter(message)
    reply_text = f'Источник: [{message.chat.title}]({message.link})'
    if is_pf:
        reply_text = f'/sent_from {message.chat.id}\n\n' + reply_text
    else:
        reply_text += (f'\n\nСообщение #отфильтровано\n'
                       f'{filter_comment}')

    await forwarded_message.reply(reply_text, disable_web_page_preview=True)
    await client.read_chat_history(message.chat.id)
    save_history(message, filter_comment if filter_comment else 'OK')


media_group_ids = {}


@Client.on_message(
    filters.media_group
    & custom_filters.monitored_channels
)
async def new_post_with_media_group(client: Client, message: Message):
    chat = media_group_ids.get(message.chat.id)
    if not chat:
        chat = media_group_ids[message.chat.id] = []
        if len(media_group_ids) > 10:
            media_group_ids.pop(list(media_group_ids.keys())[0])

    filter_comment = ''
    if message.media_group_id not in chat:
        chat.append(message.media_group_id)

        messages_id_media_group = await message.get_media_group()

        is_pf = False
        for item in messages_id_media_group:
            is_pf, filter_comment = await is_passed_filter(item)
            if not is_pf:
                break

        messages_id_media_group = [item.id
                                   for item in messages_id_media_group]
        forwarded_messages = await client.forward_messages(
            AGGREGATOR_CHANNEL, message.chat.id, messages_id_media_group)

        reply_text = f'Источник: [{message.chat.title}]({message.link})'
        if is_pf:
            reply_text = f'/sent_from {message.chat.id}\n' + reply_text
        else:
            reply_text += (f'\n\nСообщение #отфильтровано\n'
                           f'{filter_comment}')

        await forwarded_messages[-1].reply(reply_text,
                                           disable_web_page_preview=True)
        await client.read_chat_history(message.chat.id)

    save_history(message, filter_comment if filter_comment else 'OK')


@Client.on_message(
    (filters.poll | filters.service)
    & custom_filters.monitored_channels
)
async def pool_and_service_messages(client: Client, message: Message):
    await client.read_chat_history(message.chat.id)
    save_history(message, 'poll' if message.poll else 'service')
