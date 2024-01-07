import re

from pyrogram.enums import ChatType
from pyrogram.types import Chat, ChatPreview, Message

from models import User
from plugins.bot.constants.text import (
    ERROR_INVALID_LENGTH,
    ERROR_INVALID_REGEX,
    ERROR_MESSAGE_IS_NOT_PHOTO,
    ERROR_MESSAGE_IS_NOT_TEXT,
    ERROR_NOT_CHANNEL,
)


def is_admin(user_id: int) -> bool:
    return User.select().where((User.id == user_id) & (User.is_admin == True)).exists()


def is_text(message: Message) -> None:
    if not message.text:
        raise ValueError(ERROR_MESSAGE_IS_NOT_TEXT)


def is_photo(message: Message) -> None:
    if not message.photo:
        raise ValueError(ERROR_MESSAGE_IS_NOT_PHOTO)


def text_length_less_than(message: Message, length: int) -> None:
    if not message.text or len(message.text) > length:
        raise ValueError(ERROR_INVALID_LENGTH.format(length=length))


def is_valid_pattern(pattern: str) -> None:
    try:
        re.compile(pattern)
    except (re.error, RecursionError) as e:
        raise ValueError(ERROR_INVALID_REGEX.format(e))


def is_channel(chat: Chat | ChatPreview) -> None:
    if (
        isinstance(chat.type, str)
        and chat.type != "channel"
        or isinstance(chat.type, ChatType)
        and chat.type != ChatType.CHANNEL
    ):
        raise ValueError(ERROR_NOT_CHANNEL)
