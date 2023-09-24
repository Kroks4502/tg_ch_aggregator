import re

import peewee
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import Message

from clients import user
from models import Category, Source
from plugins.bot import router
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.chat_info import get_chat_info
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(initial_text="⏳ Проверка…", send_to_admins=True)
async def add_source_waiting_input(  # noqa: C901
    message: Message,
    menu: Menu,
):
    try:
        if message.forward_from_chat:
            chat = message.forward_from_chat
        else:
            try:
                # ID, публичные имена, частные ссылки (https://t.me/+klis1as0RHthMDRi)
                chat = await user.get_chat(message.text)
            except RPCError:
                # Публичная ссылка (https://t.me/mychannel)
                input_text = re.sub("https://t.me/", "", message.text)
                chat = await user.get_chat(input_text)
    except RPCError as e:
        raise ValueError(f"❌ Что-то пошло не так\n\n{e}")

    if chat.type != ChatType.CHANNEL:
        raise ValueError("❌ Это не канал")

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        raise ValueError(f"❌ Основной клиент не может подписаться на канал\n\n{e}")

    category_id = menu.path.get_value("c")
    try:
        source_obj = Source.create(id=chat.id, title=chat.title, category=category_id)
    except peewee.IntegrityError:
        raise ValueError("❗️Этот канал уже используется")

    category_obj: Category = Category.get(category_id)
    src_link = await get_channel_formatted_link(source_obj.id)
    cat_link = await get_channel_formatted_link(category_obj.id)

    warnings = await get_chat_info(source_obj)
    return (
        f"✅ Источник **{src_link}** добавлен в категорию **{cat_link}**\n\n{warnings}"
    )


@router.page(
    path=r"/c/-\d+/s/:add/",
    reply=True,
    add_wait_for_input=add_source_waiting_input,
)
async def add_source():
    return (
        "ОК. Ты добавляешь новый источник.\n\n"
        "**Введи публичное имя канала, частную ссылку, "
        f"ID, перешли сообщение из него** или {CANCEL}"
    )
