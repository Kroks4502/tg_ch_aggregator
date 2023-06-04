import inspect
import logging
import re

from pyrogram import Client, filters
from pyrogram.errors import BadRequest, MessageIdInvalid
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
from plugins.user.utils import custom_filters
from plugins.user.utils.blocking import blocking_received_media_groups
from plugins.user.utils.history import add_to_category_history
from plugins.user.utils.inspector import is_new_and_valid_post
from plugins.user.utils.rewriter import delete_agent_text_in_message
from plugins.user.utils.send_media_group import send_media_group


@Client.on_message(
    custom_filters.monitored_channels & filters.media_group & ~filters.service,
)
async def message_with_media_group(
    client: Client,
    message: Message,
    *,
    is_resending: bool = False,
):
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
                    for key in [
                        *inspect.signature(entity.type.value).parameters.keys()
                    ]:
                        entity_params.update({key: possible_entity_params[key]})
                    raw_caption_entities.append(entity.type.value(**entity_params))
                if m.photo:
                    media.append(
                        InputMediaPhoto(
                            media=m.photo.file_id,
                            parse_mode=None,
                            caption=m.caption,
                            caption_entities=raw_caption_entities,
                        )
                    )
                elif m.audio:
                    media.append(
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
                    media.append(
                        InputMediaDocument(
                            media=m.document.file_id,
                            caption=m.caption,
                            caption_entities=raw_caption_entities,
                        )
                    )
                elif m.video:
                    media.append(
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
            f'Сообщения {[item.id for item in media_group_messages]} медиагруппы'
            f' {message.media_group_id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} пересланы'
            f' в категорию {source.category.title} {source.category.tg_id}'
        )
    except MessageIdInvalid as e:
        # Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника.
        logging.warning(
            f'Сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} привело к'
            f' ошибке {e}'
        )
    # todo: делать не пересылку когда
    #  [400 CHAT_FORWARDS_RESTRICTED] - The chat restricts forwarding content (caused by "messages.ForwardMessages")
    except BadRequest as e:
        logging.error(
            (
                f'Сообщение {message.id} из источника'
                f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} привело'
                f' к ошибке\n{e}\nПолное сообщение: {message}\n'
            ),
            exc_info=True,
        )
