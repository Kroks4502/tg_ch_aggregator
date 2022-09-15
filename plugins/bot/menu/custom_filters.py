from pyrogram import filters
from pyrogram.filters import Filter
from pyrogram.types import Message


def chat(chat_id: int) -> Filter:
    async def func(flt, _, message: Message):
        return flt.chat_id == message.chat.id
    return filters.create(func, chat_id=chat_id)


def is_command(_, __, message: Message) -> bool:
    if not message.text:
        return False
    return message.text[0] == '/'


command_message = filters.create(is_command)
