import inspect

from pyrogram.enums import MessageMediaType, ParseMode
from pyrogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from plugins.user.exceptions import MessageMediaWithoutCaptionError, Operation


def tg_len(text: str) -> int:
    """Возвращает длину текста, соответствующую Telegram API."""
    return len(text.encode('utf-16-le')) // 2


def is_media_message_with_caption(operation: Operation, message: Message):
    """
    Сообщение является медиа с возможностью подписи.

    :raise MessageMediaWithoutCaptionError: Сообщение является медиа, но не может содержать подпись.
    """
    if not message.media:
        return False

    if message.media in (
        MessageMediaType.VOICE,
        MessageMediaType.VIDEO,
        MessageMediaType.AUDIO,
        MessageMediaType.PHOTO,
        MessageMediaType.DOCUMENT,
    ):
        return True

    raise MessageMediaWithoutCaptionError(operation=operation, message=message)


def get_input_media(
    message: Message,
) -> InputMediaPhoto | InputMediaAudio | InputMediaDocument | InputMediaVideo:
    raw_caption_entities = []
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
    # raw_caption_entities = message.caption_entities todo del
    if message.photo:
        return InputMediaPhoto(
            media=message.photo.file_id,
            caption=message.caption,
            parse_mode=ParseMode.DISABLED,
            caption_entities=raw_caption_entities,
            has_spoiler=message.has_media_spoiler,  # todo NEW check !
        )

    if message.audio:
        return InputMediaAudio(
            media=message.audio.file_id,
            thumb=message.audio.thumbs,  # todo NEW check !
            caption=message.caption,
            parse_mode=ParseMode.DISABLED,
            caption_entities=raw_caption_entities,
            duration=message.audio.duration,
            performer=message.audio.performer,
            title=message.audio.title,
        )

    if message.document:
        return InputMediaDocument(
            media=message.document.file_id,
            thumb=message.document.thumbs,  # todo NEW check !
            caption=message.caption,
            parse_mode=ParseMode.DISABLED,
            caption_entities=raw_caption_entities,
        )

    if message.video:
        return InputMediaVideo(
            media=message.video.file_id,
            thumb=message.video.thumbs,  # todo NEW check !
            caption=message.caption,
            parse_mode=ParseMode.DISABLED,
            caption_entities=raw_caption_entities,
            width=message.video.width,
            height=message.video.height,
            duration=message.video.duration,
            supports_streaming=message.video.supports_streaming,
            has_spoiler=message.has_media_spoiler,  # todo NEW check !
        )

    raise ValueError(f'Message with this type {message.media} can`t be copied.')
