import inspect

from pyrogram.types import (
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from models import Source
from plugins.user.exceptions import (
    MessageBlockedByIdError,
    MessageBlockedByMediaGroupError,
)
from plugins.user.types import Operation
from plugins.user.utils.chats_locks import ChatsLocks, MessagesLocks
from plugins.user.utils.inspector import FilterInspector
from plugins.user.utils.rewriter.footer import LINK_TEXT, FooterController
from plugins.user.utils.rewriter.header import (
    FWD_TEXT_TMPL,
    SRC_TEXT_TMPL,
    HeaderController,
)
from plugins.user.utils.text_length import tg_len
from settings import TELEGRAM_MAX_CAPTION_LENGTH, TELEGRAM_MAX_TEXT_LENGTH

blocking_messages = ChatsLocks("all")


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

    if filter_obj := inspector.check_message_type():
        return filter_obj.id

    if message.text or message.caption:
        if filter_obj := inspector.check_white_text():
            return filter_obj.id
        if filter_obj := inspector.check_text():
            return filter_obj.id

    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if filter_obj := inspector.check_entities(entity):
                return filter_obj.id

    return  # noqa: R502


def get_input_media(
    message: Message,
) -> InputMediaPhoto | InputMediaAudio | InputMediaDocument | InputMediaVideo:
    raw_caption_entities = []
    # При использовании методов EditMessageMedia.edit_message_media и SendMediaGroup.send_media_group
    # InputMedia*** в caption_entities принимает только raw.types.MessageEntity***, а не types.MessageEntity
    for entity in message.caption_entities or []:
        possible_entity_params = {
            "offset": entity.offset,
            "length": entity.length,
            "user_id": entity.user.id if entity.user else 0,
            "language": entity.language,
            "url": entity.url,
            "document_id": entity.custom_emoji_id,
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

    raise ValueError(f"Message with this type {message.media} can`t be copied.")


def cut_long_message(message: Message):
    if tg_len(message.text or message.caption) <= (
        TELEGRAM_MAX_TEXT_LENGTH if message.text else TELEGRAM_MAX_CAPTION_LENGTH
    ):
        return

    footer = FooterController()
    footer.add_item(
        text=LINK_TEXT,
        url=(
            message.link
            if not message.forward_from_chat
            else get_fwd_message_link(message)
        ),
        bold=True,
    )
    footer.include_to_message(message=message)


def add_header(source: Source, message: Message):
    header = HeaderController(item_separator="\n")
    header.add_item(
        text=SRC_TEXT_TMPL.format(
            source.title_alias or message.chat.title or message.chat.id
        ),
        bold=True,
        url=message.link,
    )

    if message.forward_from_chat:
        header.add_item(
            text=FWD_TEXT_TMPL.format(
                message.forward_from_chat.title or message.forward_from_chat.id
            ),
            url=get_fwd_message_link(message),
        )

    header.include_to_message(message=message, end_text="\n\n")


def get_fwd_message_link(message: Message):
    username = message.forward_from_chat.username
    if not username:
        for un in message.forward_from_chat.usernames or ():
            if un.active:
                username = un.username
                break

    if not username:
        username = message.forward_from_chat.id

    return f"https://t.me/{username}/{message.forward_from_message_id}"
