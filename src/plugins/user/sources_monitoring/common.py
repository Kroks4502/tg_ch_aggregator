import inspect

from pyrogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from plugins.user.exceptions import (
    MessageBlockedByIdError,
    MessageBlockedByMediaGroupError,
    Operation,
)
from plugins.user.utils.chats_locks import ChatsLocks, MessagesLocks
from plugins.user.utils.inspector import FilterInspector

blocking_messages = ChatsLocks('all')


def set_blocking(
    operation: Operation, message: Message, block_value: int
) -> MessagesLocks:
    """
    Установить блокировку для сущности.

    :param operation: Производимая операция (для исключения).
    :param message: Сообщение источника (для исключения).
    :param block_value: ID для блокировки (message.id или message.media_group_id).
    :raise MessageBlockedByMediaGroupError: Сообщение заблокировано в составе медиагруппы.
    :raise MessageBlockedByIdError: Сообщение заблокировано по ID
    :return:
    """
    blocked = blocking_messages.get(key=message.chat.id)
    if blocked.contains(key=message.media_group_id):
        raise MessageBlockedByMediaGroupError(
            operation=operation, message=message, blocked=blocked
        )
    if blocked.contains(key=message.id):
        raise MessageBlockedByIdError(
            operation=operation, message=message, blocked=blocked
        )
    blocked.add(value=block_value)
    return blocked


def get_filter_id_or_none(message: Message, source_id: int) -> int | None:
    """Получить ID фильтра, который не прошёл текст сообщения."""
    inspector = FilterInspector(message=message, source_id=source_id)

    if result := inspector.check_message_type():
        return result['id']

    if message.text or message.caption:
        if result := inspector.check_white_text():
            return result['id']
        if result := inspector.check_text():
            return result['id']

    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if result := inspector.check_entities(entity):
                return result['id']

    return  # noqa R502


def get_input_media(
    message: Message,
) -> InputMediaPhoto | InputMediaAudio | InputMediaDocument | InputMediaVideo:
    raw_caption_entities = []
    # При использовании методов EditMessageMedia.edit_message_media и SendMediaGroup.send_media_group
    # InputMedia*** в caption_entities принимает только raw.types.MessageEntity***, а не types.MessageEntity
    for entity in message.caption_entities or []:
        possible_entity_params = {
            'offset': entity.offset,
            'length': entity.length,
            'user_id': entity.user.id if entity.user else 0,
            'language': entity.language,
            'url': entity.url,
            'document_id': entity.custom_emoji_id,
        }
        entity_params = {}
        for key in inspect.signature(entity.type.value).parameters.keys():
            entity_params.update({key: possible_entity_params[key]})
        raw_caption_entities.append(entity.type.value(**entity_params))

    if message.photo:
        return InputMediaPhoto(
            media=message.photo.file_id,
            caption=message.caption,
            parse_mode=None,
            caption_entities=raw_caption_entities,
            has_spoiler=message.has_media_spoiler,
        )

    if message.audio:
        return InputMediaAudio(
            media=message.audio.file_id,
            thumb=message.audio.thumbs,
            caption=message.caption,
            parse_mode=None,
            caption_entities=raw_caption_entities,
            duration=message.audio.duration,
            performer=message.audio.performer,
            title=message.audio.title,
        )

    if message.document:
        return InputMediaDocument(
            media=message.document.file_id,
            thumb=message.document.thumbs,
            caption=message.caption,
            parse_mode=None,
            caption_entities=raw_caption_entities,
        )

    if message.video:
        return InputMediaVideo(
            media=message.video.file_id,
            thumb=message.video.thumbs,
            caption=message.caption,
            parse_mode=None,
            caption_entities=raw_caption_entities,
            width=message.video.width,
            height=message.video.height,
            duration=message.video.duration,
            supports_streaming=message.video.supports_streaming,
            has_spoiler=message.has_media_spoiler,
        )

    raise ValueError(f'Message with this type {message.media} can`t be copied.')
