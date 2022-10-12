import inspect
import re
from typing import Match

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import (Message, InputMediaPhoto, InputMediaVideo,
                            InputMediaAudio, InputMediaDocument, MessageEntity)

from log import logger
from models import Source, CategoryMessageHistory
from plugins.user import custom_filters
from plugins.user.helpers import (add_to_filter_history,
                                  add_to_category_history,
                                  get_message_link,
                                  perform_check_history, perform_filtering)
from send_media_group import send_media_group
from settings import PATTERN_AGENT

media_group_ids = {}  # chat_id: [media_group_id ...]


def is_new_and_valid_post(message: Message, source: Source) -> bool:
    if h_obj := perform_check_history(message, source):
        logger.info(
            f'Сообщение {message.id} из чата '
            f'{message.chat.id} ({message.link}) '
            f'уже есть в канале категории {source.category} '
            f'({get_message_link(h_obj.category.tg_id, h_obj.message_id)})')
        return False

    if filter_id := perform_filtering(message, source):
        add_to_filter_history(message, filter_id, source)
        logger.info(
            f'Сообщение {message.id} из чата '
            f'{message.chat.id} ({message.link}) '
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

    search_result = re.search(
        PATTERN_AGENT, message.text or message.caption or '')
    if search_result:
        delete_agent_text_in_message(search_result, message)
        forwarded_message = await message.copy(source.category.tg_id)
    else:
        forwarded_message = await message.forward(source.category.tg_id)

    add_to_category_history(
        message, forwarded_message, source,
        rewritten=True if search_result else False)

    await client.read_chat_history(message.chat.id)
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
    search_result = None
    for m in media_group_messages:
        if not is_new_and_valid_post(m, source):
            return
        if m.caption:
            search_result = re.search(PATTERN_AGENT, m.caption)
            if search_result:
                delete_agent_text_in_message(search_result, m)

    if search_result:
        media = []
        for m in media_group_messages:
            raw_caption_entities = []
            for entity in (m.caption_entities if m.caption_entities else []):
                possible_entity_params = {
                    'offset': entity.offset,
                    'length': entity.length,
                    'user_id': entity.user.id if entity.user else 0,
                    'language': entity.language,
                    'url': entity.url,
                    'document_id': entity.custom_emoji_id
                }
                entity_params = {}
                for key in [*inspect.signature(
                        entity.type.value).parameters.keys()]:
                    entity_params.update({key: possible_entity_params[key]})
                raw_caption_entities.append(entity.type.value(**entity_params))
            if m.photo:
                media.append(InputMediaPhoto(
                    media=m.photo.file_id,
                    parse_mode=None,
                    caption=m.caption,
                    caption_entities=raw_caption_entities
                ))
            elif m.audio:
                media.append(InputMediaAudio(
                    media=m.audio.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                    duration=m.audio.duration,
                    performer=m.audio.performer,
                    title=m.audio.title
                ))
            elif m.document:
                media.append(InputMediaDocument(
                    media=m.document.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                ))
            elif m.video:
                media.append(InputMediaVideo(
                    media=m.video.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                    width=m.video.width,
                    height=m.video.height,
                    duration=m.video.duration,
                    supports_streaming=m.video.supports_streaming,
                ))
            else:
                raise ValueError('Message with this type can`t be copied.')
        forwarded_messages = await send_media_group(
            client,
            source.category.tg_id,
            media=media,
        )
    else:
        forwarded_messages = await client.forward_messages(
            source.category.tg_id, message.chat.id,
            [item.id for item in media_group_messages])

    for original_message, forward_message in zip(
            media_group_messages, forwarded_messages):
        add_to_category_history(
            original_message, forward_message, source,
            rewritten=True if search_result else False)

    await client.read_chat_history(message.chat.id)
    logger.debug(f'Сообщение {message.id} '
                 f'из источника {source.title} '
                 f'переслано в категорию {source.category.title}')


def delete_agent_text_in_message(search_result: Match, message: Message):
    separator = '\n\n'
    author = f'💬 Источник: {message.chat.title}\n\n'
    if message.forward_date:
        author = f'💬 Источник: {message.forward_from_chat.title}\n\n'
    if message.text:
        message.text = (author + message.text[:search_result.start()]
                        + separator + message.text[search_result.end():])
    elif message.caption:
        message.caption = (author + message.caption[:search_result.start()]
                           + separator + message.caption[search_result.end():])

    cut_text_len = search_result.end() - search_result.start() - len(separator)
    for entity in (message.entities or message.caption_entities or []):
        if entity.offset > search_result.start():
            entity.offset -= cut_text_len

    add_author_len = len(author)
    for entity in (message.entities or message.caption_entities or []):
        entity.offset += add_author_len

    bold = MessageEntity(
        type=MessageEntityType.BOLD, offset=0, length=add_author_len)
    url = message.link
    if message.forward_date and message.forward_from_chat.username:
        url = (f'https://t.me/{message.forward_from_chat.username}/'
               f'{message.forward_from_message_id}')
    text_link = MessageEntity(
        type=MessageEntityType.TEXT_LINK, offset=0, length=add_author_len,
        url=url)
    if message.text:
        if not message.entities:
            message.entities = []
        message.entities.insert(0, bold)
        message.entities.insert(0, text_link)
    if message.caption:
        if not message.caption_entities:
            message.caption_entities = []
        message.caption_entities.insert(0, bold)
        message.caption_entities.insert(0, text_link)


@Client.on_message(
    custom_filters.monitored_channels
    & filters.service
)
async def service_message(client: Client, message: Message):
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
        for m in await client.get_media_group(
                history_obj.category.tg_id, history_obj.message_id):
            messages_to_delete.append(m.id)
    else:
        messages_to_delete = [history_obj.message_id]

    await client.delete_messages(
        history_obj.category.tg_id, messages_to_delete)

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
    for message in messages:
        history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
            source=Source.get_or_none(tg_id=message.chat.id),
            source_message_id=message.id,
            deleted=False, )
        if history_obj:
            await client.delete_messages(
                history_obj.category.tg_id, history_obj.message_id)
            history_obj.source_message_deleted = True
            history_obj.deleted = True
            history_obj.save()
            logger.debug(f'Сообщение {history_obj.source_message_id} '
                         f'из источника {history_obj.source.title} было удалено. '
                         f'Оно удалено из категории {history_obj.category.title}')
