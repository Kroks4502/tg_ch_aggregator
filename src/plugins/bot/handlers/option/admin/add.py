import peewee
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import Message

from models import User
from plugins.bot import router
from plugins.bot.constants import CANCEL
from plugins.bot.utils.links import get_user_formatted_link


@router.wait_input(send_to_admins=True)
async def add_admin_waiting_input(
    client: Client,
    message: Message,
):
    try:
        chat = await client.get_chat(message.text)
    except RPCError as e:
        raise ValueError(f"❌ Что-то пошло не так\n\n{e}")

    if chat.type != ChatType.PRIVATE:
        raise ValueError("❌ Это не пользователь")

    if chat.username:
        username = chat.username
    else:
        username = (
            f'{chat.first_name + " " if chat.first_name else ""}'
            f'{chat.last_name + " " if chat.last_name else ""}'
        )
    try:
        admin_obj = User.create(id=chat.id, username=username, is_admin=True)
    except peewee.IntegrityError:
        raise ValueError("❗️Этот пользователь уже администратор")

    adm_link = await get_user_formatted_link(admin_obj.id)

    return f"✅ Администратор **{adm_link}** добавлен"


@router.page(
    path=r"/a/:add/",
    reply=True,
    add_wait_for_input=add_admin_waiting_input,
)
async def add_admin():
    return (
        "ОК. Ты добавляешь нового администратора.\n\n"
        f"**Введи ID или имя пользователя** или {CANCEL}"
    )
