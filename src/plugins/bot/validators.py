import re

from pyrogram.types import Message

from models import User


def is_admin(user_id: int) -> bool:
    return User.select().where((User.id == user_id) & (User.is_admin == True)).exists()


def is_text(message: Message) -> None:
    if not message.text:
        raise ValueError("❌ Допустимо только текстовое сообщение")


def is_photo(message: Message) -> None:
    if not message.photo:
        raise ValueError("❌ Допустимо только сообщение с изображением")


def text_length_less_than(message: Message, length: int) -> None:
    if not message.text or len(message.text) > length:
        raise ValueError(f"❌ Количество символов не должно превышать {length}")


def is_valid_pattern(pattern: str) -> None:
    try:
        re.compile(pattern)
    except (re.error, RecursionError):
        raise ValueError("❌ Невалидное регулярное выражение")
