import inspect
import logging
import re

from pyrogram import Client, filters
from pyrogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from common import get_shortened_text
from config import PATTERN_AGENT
from models import Source
from plugins.user.sources_monitoring.new_message.common import (
    handle_errors_on_new_message,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.blocking import blocking_received_media_groups
from plugins.user.utils.history import add_to_category_history
from plugins.user.utils.inspector import is_new_and_valid_post
from plugins.user.utils.rewriter import delete_agent_text_in_message
from plugins.user.utils.send_media_group import send_media_group


@Client.on_message(
    custom_filters.monitored_channels & filters.media_group & ~filters.service,
)
@handle_errors_on_new_message
async def new_media_group_message(
    client: Client,
    message: Message,
    *,
    is_resending: bool = False,
):
    logging_on_startup(message, is_resending)

    blocked = blocking_received_media_groups.get(message.chat.id)
    if blocked.contains(message.media_group_id):
        return
    blocked.add(message.media_group_id)

    source = Source.get(tg_id=message.chat.id)

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
        media = get_new_media(media_group_messages)
        forwarded_messages = await send_media_group(
            client,
            source.category.tg_id,
            media=media,
            disable_notification=is_resending,
        )
    else:
        forwarded_messages = await client.forward_messages(
            source.category.tg_id,
            message.chat.id,
            [item.id for item in media_group_messages],
            disable_notification=is_resending,
        )

    for original_message, forward_message in zip(
        media_group_messages, forwarded_messages
    ):
        add_to_category_history(
            original_message, forward_message, source, rewritten=is_agent
        )

    await client.read_chat_history(message.chat.id)
    logging.info(
        f'Сообщения {[item.id for item in media_group_messages]} медиагруппы '
        f'{message.media_group_id} из источника '
        f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} пересланы '
        f'в категорию {source.category.title} {source.category.tg_id}'
    )


def logging_on_startup(message: Message, is_resending: bool):
    if not is_resending:
        logging.debug(
            f'Источник {get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'отправил сообщение {message.id} '
            f'в составе медиагруппы {message.media_group_id}'
        )
    else:
        logging.debug(
            'Повторная отправка из источника '
            f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'сообщения {message.id} '
            f'в составе медиагруппы {message.media_group_id}'
        )


def get_new_media(
    source_media_messages: list[Message],
) -> list[InputMediaPhoto | InputMediaAudio | InputMediaDocument | InputMediaVideo]:
    new_media_messages = []
    for m in source_media_messages:
        raw_caption_entities = []
        for entity in m.caption_entities if m.caption_entities else []:
            possible_entity_params = {
                'offset': entity.offset,
                'length': entity.length,
                'user_id': entity.user.id if entity.user else 0,
                'language': entity.language,
                'url': entity.url,
                'document_id': entity.custom_emoji_id,
            }
            entity_params = {}
            for key in [*inspect.signature(entity.type.value).parameters.keys()]:
                entity_params.update({key: possible_entity_params[key]})
            raw_caption_entities.append(entity.type.value(**entity_params))
        if m.photo:
            new_media_messages.append(
                InputMediaPhoto(
                    media=m.photo.file_id,
                    parse_mode=None,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                )
            )
        elif m.audio:
            new_media_messages.append(
                InputMediaAudio(
                    media=m.audio.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                    duration=m.audio.duration,
                    performer=m.audio.performer,
                    title=m.audio.title,
                )
            )
        elif m.document:
            new_media_messages.append(
                InputMediaDocument(
                    media=m.document.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                )
            )
        elif m.video:
            new_media_messages.append(
                InputMediaVideo(
                    media=m.video.file_id,
                    caption=m.caption,
                    caption_entities=raw_caption_entities,
                    width=m.video.width,
                    height=m.video.height,
                    duration=m.video.duration,
                    supports_streaming=m.video.supports_streaming,
                )
            )
        else:
            raise ValueError('Message with this type can`t be copied.')
    return new_media_messages
