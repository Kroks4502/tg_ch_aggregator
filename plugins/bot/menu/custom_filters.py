from pyrogram import filters
from pyrogram.types import Message, CallbackQuery

from plugins.bot.menu.helpers.checks import is_admin


def chat(chat_id: int):
    async def func(flt, _, message: Message):
        return flt.chat_id == message.chat.id
    return filters.create(func, chat_id=chat_id)


def is_command(_, __, message: Message) -> bool:
    if not message.text:
        return False
    return str(message.text)[0] == '/'


command_message = filters.create(is_command)


def is_admin_f(_, __, callback_query: CallbackQuery | Message):
    return is_admin(callback_query.from_user.id)


admin_only = filters.create(is_admin_f)
