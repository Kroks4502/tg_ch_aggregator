import peewee
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import Message

from models import User
from plugins.bot import router
from plugins.bot.constants.text import ERROR_UNKNOWN
from plugins.bot.handlers.option.admin.common.constants import (
    DIALOG_ADD_TEXT,
    ERROR_NOT_USER,
    ERROR_USER_IS_ADMIN,
)
from plugins.bot.handlers.option.admin.common.utils import get_user_menu_success_text


@router.wait_input(send_to_admins=True)
async def add_user_waiting_input(
    client: Client,
    message: Message,
):
    try:
        chat = await client.get_chat(message.text)
    except RPCError as e:
        raise ValueError(f"{ERROR_UNKNOWN}\n\n{e}")

    if chat.type != ChatType.PRIVATE:
        raise ValueError(ERROR_NOT_USER)

    if chat.username:
        username = chat.username
    else:
        username = (
            f'{chat.first_name + " " if chat.first_name else ""}'
            f'{chat.last_name + " " if chat.last_name else ""}'
        )
    try:
        user_obj = User.create(id=chat.id, username=username, is_admin=True)
    except peewee.IntegrityError:
        raise ValueError(ERROR_USER_IS_ADMIN)

    return await get_user_menu_success_text(user_id=user_obj.id, action="добавлен")


@router.page(
    path=r"/u/:add/",
    reply=True,
    add_wait_for_input=add_user_waiting_input,
)
async def add_user():
    return DIALOG_ADD_TEXT
