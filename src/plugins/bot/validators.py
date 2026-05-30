import re

from telethon.tl.types import Channel

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


def is_text(message) -> None:
    if not message.text:
        raise ValueError(ERROR_MESSAGE_IS_NOT_TEXT)


def is_photo(message) -> None:
    if not message.photo:
        raise ValueError(ERROR_MESSAGE_IS_NOT_PHOTO)


def text_length_less_than(message, length: int) -> None:
    if not message.text or len(message.text) > length:
        raise ValueError(ERROR_INVALID_LENGTH.format(length=length))


def is_valid_pattern(pattern: str) -> None:
    try:
        re.compile(pattern)
    except (re.error, RecursionError) as e:
        raise ValueError(ERROR_INVALID_REGEX.format(e))


def is_channel(entity) -> None:
    """Проверить, что сущность является Telegram-каналом (не группой и не пользователем)."""
    if not isinstance(entity, Channel):
        raise ValueError(ERROR_NOT_CHANNEL)
