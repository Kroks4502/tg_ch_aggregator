import re

import peewee
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError, exceptions
from pyrogram.types import Message

from clients import user
from models import Category
from plugins.bot import router
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(back_step=2, initial_text="⏳ Проверка…", send_to_admins=True)
async def edit_category_channel_waiting_input(  # noqa: C901
    client: Client,
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
        member = await chat.get_member(client.me.id)
        if not member.privileges.can_post_messages:
            raise ValueError("❌ Бот не имеет прав на публикацию в этом канале")
    except exceptions.bad_request_400.UserNotParticipant:
        raise ValueError("❌ Бот не администратор этого канала")

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        raise ValueError(f"❌ Основной клиент не может подписаться на канал\n\n{e}")

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    cat_link_old = await get_channel_formatted_link(category_obj.id)

    category_obj.id = chat.id
    category_obj.title = chat.title
    try:
        category_obj.save()
    except peewee.IntegrityError:
        raise ValueError("❗️Этот канал уже используется")

    cat_link_new = await get_channel_formatted_link(category_obj.id)
    return f"✅ Категория **{cat_link_old}** изменена на **{cat_link_new}**"


@router.page(
    path=r"/c/-\d+/:edit/channel/",
    reply=True,
    add_wait_for_input=edit_category_channel_waiting_input,
)
async def edit_category_channel():
    return (
        "ОК. Ты меняешь канал для категории, "
        "в который будут пересылаться сообщения из источников. "
        "Этот бот должен быть администратором канала "
        "с возможностью публиковать записи.\n\n"
        "**Введи публичное имя канала, частную ссылку, "
        f"ID, перешли сообщение из него** или {CANCEL}"
    )
