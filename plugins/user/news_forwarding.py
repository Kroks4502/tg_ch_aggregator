import inspect
import re
from typing import Match

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType
from pyrogram.errors import BadRequest
from pyrogram.types import (Message, InputMediaPhoto, InputMediaVideo,
                            InputMediaAudio, InputMediaDocument, MessageEntity)

from log import logger
from models import Source, CategoryMessageHistory
from plugins.user import custom_filters
from plugins.user.helpers import (add_to_filter_history,
                                  add_to_category_history,
                                  get_message_link,
                                  perform_check_history, perform_filtering, ChatsLocks)
from send_media_group import send_media_group
from settings import PATTERN_AGENT, PATTERN_WITHOUT_SMILE, MESSAGES_EDIT_LIMIT_TD


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
async def message_without_media_group(client: Client, message: Message, *, disable_notification: bool = None):
    source = Source.get(tg_id=message.chat.id)

    if not is_new_and_valid_post(message, source):
        await client.read_chat_history(message.chat.id)
        return

    message_text = message.text or message.caption or ''
    search_result = re.search(
        PATTERN_AGENT, str(message_text))
    try:
        if search_result:
            delete_agent_text_in_message(search_result, message)
            forwarded_message = await message.copy(
                source.category.tg_id, disable_notification=disable_notification)
        else:
            forwarded_message = await message.forward(
                source.category.tg_id, disable_notification=disable_notification)

        add_to_category_history(
            message, forwarded_message, source,
            rewritten=bool(search_result))

        await client.read_chat_history(message.chat.id)
        logger.info(f'Сообщение {message.id} '
                    f'из источника {source.title} '
                    f'переслано в категорию {source.category.title}')
    except BadRequest as e:
        logger.error(f'Сообщение {message.id} '
                     f'из источника {message.chat.title} привело к ошибке: {e}\n'
                     f'Полное сообщение: {message}\n', exc_info=True)


blocking_received_media_groups = ChatsLocks()


@Client.on_message(
    custom_filters.monitored_channels
    & filters.media_group
    & ~filters.service
)
async def message_with_media_group(client: Client, message: Message, *, disable_notification: bool = False):
    blocked = blocking_received_media_groups.get(message.chat.id)
    if blocked.contains(message.media_group_id):
        return
    blocked.add(message.media_group_id)

    source = Source.get(tg_id=message.chat.id)
    try:
        media_group_messages = await message.get_media_group()
        is_agent = False
        for m in media_group_messages:
            if not is_new_and_valid_post(m, source):
                await client.read_chat_history(message.chat.id)
                return
            if m.caption:
                search_result = re.search(PATTERN_AGENT, str(m.caption))
                if search_result:
                    is_agent = True
                    delete_agent_text_in_message(search_result, m)

        if is_agent:
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
                disable_notification=disable_notification
            )
        else:
            forwarded_messages = await client.forward_messages(
                source.category.tg_id, message.chat.id,
                [item.id for item in media_group_messages],
                disable_notification=disable_notification
            )

        for original_message, forward_message in zip(
                media_group_messages, forwarded_messages):
            add_to_category_history(
                original_message, forward_message, source,
                rewritten=is_agent)

        await client.read_chat_history(message.chat.id)
        logger.info(f'Сообщения {[item.id for item in media_group_messages]} медиагруппы {message.media_group_id} '
                    f'из источника {source.title} '
                    f'пересланы в категорию {source.category.title}')
    except BadRequest as e:
        logger.error(f'Сообщение {message.id} '
                     f'из источника {message.chat.title} привело к ошибке: {e}\n'
                     f'Полное сообщение: {message}\n', exc_info=True)


def delete_agent_text_in_message(search_result: Match, message: Message):
    separator = '\n\n'
    title = re.sub(PATTERN_WITHOUT_SMILE, "",
                   message.forward_from_chat.title if message.forward_date else message.chat.title)
    author = (f'💬 Источник: '
              f'{title if title else message.chat.id}'
              f'\n\n')
    start = search_result.start()
    end = search_result.end()
    if message.text:
        message.text = str(message.text)
        message.text = (author + message.text[:start]
                        + f'{separator if start != 0 else ""}' + message.text[end:])
    elif message.caption:
        message.caption = str(message.caption)
        message.caption = (author + message.caption[:start]
                           + f'{separator if start != 0 else ""}' + message.caption[end:])

    cut_text_len = search_result.end() - search_result.start() - len(separator)
    for entity in (message.entities or message.caption_entities or []):
        if entity.offset > search_result.start():
            entity.offset -= cut_text_len

    add_author_len = len(author)
    for entity in (message.entities or message.caption_entities or []):
        entity.offset += add_author_len + 1

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


blocking_editable_messages = ChatsLocks()


@Client.on_edited_message(
    custom_filters.monitored_channels
)
async def edited_message(client: Client, message: Message):
    if message.edit_date - message.date > MESSAGES_EDIT_LIMIT_TD:
        logger.warning(f'Изменено сообщение {message.id} '
                       f'из источника {message.chat.title} '
                       f'за пределами ограничения {MESSAGES_EDIT_LIMIT_TD}. ')
        return

    blocked = blocking_editable_messages.get(message.chat.id)
    if (blocked.contains(message.media_group_id)
            or blocked.contains(message.id)):
        logger.warning(f'Изменение сообщения {message.id} '
                       f'из источника {message.chat.title} заблокировано. ')
        return
    blocked.add(message.media_group_id if message.media_group_id else message.id)

    history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
        source=Source.get_or_none(tg_id=message.chat.id),
        source_message_id=message.id,
        deleted=False, )
    if not history_obj:
        logger.warning(f'Измененного сообщения {message.id} '
                       f'из источника {message.chat.title} нет в истории. ')
        blocked.remove(message.media_group_id if message.media_group_id else message.id)
        return

    if history_obj.media_group:
        messages_to_delete = []
        query = (CategoryMessageHistory
                 .select()
                 .where((CategoryMessageHistory.source == history_obj.source)
                        & (CategoryMessageHistory.media_group == history_obj.media_group)
                        & (CategoryMessageHistory.deleted == False)))
        for m in query:
            messages_to_delete.append(m.message_id)
    else:
        messages_to_delete = [history_obj.message_id]

    if messages_to_delete:
        await client.delete_messages(
            history_obj.category.tg_id, messages_to_delete)

        query = ((CategoryMessageHistory
                  .select()
                  .where((CategoryMessageHistory.category == history_obj.category)
                         & (CategoryMessageHistory.message_id << messages_to_delete)))
                 if history_obj.media_group else [history_obj])
        for h in query:
            h.source_message_edited = True
            h.deleted = True
            h.save()
            logger.info(f'Сообщение {h.source_message_id} '
                        f'из источника {h.source.title} было изменено. '
                        f'Оно удалено из категории {h.category.title}')

        if message.media_group_id:
            if b := blocking_received_media_groups.get(message.chat.id):
                b.remove(message.media_group_id)
            await message_with_media_group(client, message, disable_notification=True)
        else:
            await message_without_media_group(client, message, disable_notification=True)

    blocked.remove(message.media_group_id if message.media_group_id else message.id)


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
            logger.info(f'Сообщение {history_obj.source_message_id} '
                        f'из источника {history_obj.source.title} было удалено. '
                        f'Оно удалено из категории {history_obj.category.title}')
