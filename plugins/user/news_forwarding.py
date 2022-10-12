from peewee import Update
from pyrogram import Client, filters
from pyrogram.types import Message, Chat

from log import logger
from models import Source, CategoryMessageHistory
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
async def message_without_media_group(client: Client, message: Message):
    source = Source.get(tg_id=message.chat.id)

    if not is_new_and_valid_post(message, source):
        return

    forwarded_message = await message.forward(source.category.tg_id)
    await client.read_chat_history(message.chat.id)
    add_to_category_history(message, forwarded_message, source)

    logger.debug(f'Сообщение {message.id} '
                 f'из источника {source.title} '
                 f'переслано в категорию {source.category.title}')


@Client.on_message(
    custom_filters.monitored_channels
    & filters.media_group
    & ~filters.service
)
async def message_with_media_group(client: Client, message: Message):
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
        source.category.tg_id, message.chat.id,
        [item.id for item in media_group_messages])
    await client.read_chat_history(message.chat.id)
    for original_message, forward_message in zip(media_group_messages, forwarded_messages):
        add_to_category_history(original_message, forward_message, source)

    logger.debug(f'Сообщение {message.id} '
                 f'из источника {source.title} '
                 f'переслано в категорию {source.category.title}')


@Client.on_message(
    custom_filters.monitored_channels
    & filters.service
)
async def service_message(client: Client, message: Message):
    logger.error('service_message')
    print(message)
    await client.read_chat_history(message.chat.id)


@Client.on_edited_message(
    custom_filters.monitored_channels
)
async def edited_message(client: Client, message: Message):
    history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
        source=Source.get_or_none(tg_id=message.chat.id),
        source_message_id=message.id,
        deleted=False,)

    if not history_obj:
        return

    if history_obj.media_group:
        messages_to_delete = []
        for m in await client.get_media_group(history_obj.category.tg_id, history_obj.message_id):
            messages_to_delete.append(m.id)
    else:
        messages_to_delete = [history_obj.message_id]

    await client.delete_messages(history_obj.category.tg_id, messages_to_delete)

    query = ((CategoryMessageHistory
             .select()
             .where((CategoryMessageHistory.source == history_obj.source)
                    & (CategoryMessageHistory.media_group == history_obj.media_group)))
             if history_obj.media_group else [history_obj])
    for h in query:
        h.source_message_edited = True
        h.deleted = True
        h.save()
        logger.debug(f'Сообщение {h.source_message_id} '
                     f'из источника {h.source.title} было изменено. '
                     f'Оно удалено из категории {h.category.title}')

    if message.media_group_id:
        media_group_ids.clear()
        await message_with_media_group(client, message)
    else:
        await message_without_media_group(client, message)


@Client.on_deleted_messages(
    custom_filters.monitored_channels
)
async def deleted_messages(client: Client, messages: list[Message]):
    logger.debug('deleted_messages')
    for message in messages:
        print(message)
        history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
            source=Source.get_or_none(tg_id=message.chat.id),
            source_message_id=message.id,
            deleted=False, )
        if history_obj:
            await client.delete_messages(history_obj.category.tg_id, history_obj.message_id)
            history_obj.source_message_deleted = True
            history_obj.deleted = True
            history_obj.save()
            logger.debug(f'Сообщение {history_obj.source_message_id} '
                         f'из источника {history_obj.source.title} было удалено. '
                         f'Оно удалено из категории {history_obj.category.title}')


# @Client.on_raw_update()
# async def raw(client: Client, update: Update, users: dict, chats: dict):
#     logger.error('RAW')
