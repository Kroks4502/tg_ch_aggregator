from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from models import User


def chat(chat_id: int):
    async def func(flt, _, message: Message):
        return flt.chat_id == message.chat.id

    return filters.create(func, chat_id=chat_id)


def command_message_filter(_, __, message: Message) -> bool:
    if not message.text:
        return False

    return str(message.text)[0] == "/"


command_message = filters.create(command_message_filter)


def admin_only_filter(_, __, obj: CallbackQuery | Message):
    return (
        User.select()
        .where((User.id == obj.from_user.id) & (User.is_admin == True))
        .exists()
    )


admin_only = filters.create(admin_only_filter)
