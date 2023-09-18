import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError, exceptions
from pyrogram.types import CallbackQuery, Message

from clients import user
from models import Category
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/:edit/channel/$") & custom_filters.admin_only,
)
async def edit_category_channel(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        "ОК. Ты меняешь канал для категории, "
        "в который будут пересылаться сообщения из источников. "
        "Этот бот должен быть администратором канала "
        "с возможностью публиковать записи.\n\n"
        "**Введи публичное имя канала, частную ссылку, "
        f"ID, перешли сообщение из него** или {CANCEL}"
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_category_channel_waiting_input,
        client,
        callback_query,
    )


async def edit_category_channel_waiting_input(  # noqa: C901
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data, back_step=2)

    #

    new_message = await message.reply_text("⏳ Проверка…")

    async def edit_text(text):
        await new_message.edit_text(
            text,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

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
        await edit_text(f"❌ Что-то пошло не так\n\n{e}")
        return

    if chat.type != ChatType.CHANNEL:
        await edit_text("❌ Это не канал")
        return

    #

    try:
        member = await chat.get_member(client.me.id)
        if not member.privileges.can_post_messages:
            await edit_text("❌ Бот не имеет прав на публикацию в этом канале")
            return
    except exceptions.bad_request_400.UserNotParticipant:
        await edit_text("❌ Бот не администратор этого канала")
        return

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        await edit_text(f"❌ Основной клиент не может подписаться на канал\n\n{e}")
        return

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    cat_link_old = await get_channel_formatted_link(category_obj.id)

    category_obj.id = chat.id
    category_obj.title = chat.title
    try:
        category_obj.save()
    except peewee.IntegrityError:
        await edit_text("❗️Этот канал уже используется")
        return

    cat_link_new = await get_channel_formatted_link(category_obj.id)
    success_text = f"✅ Категория **{cat_link_old}** изменена на **{cat_link_new}**"
    await edit_text(success_text)

    await send_message_to_admins(client, callback_query, success_text)
