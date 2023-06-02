import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Message

from clients import user
from models import Category, Source
from plugins.bot.utils import custom_filters
from plugins.bot.utils.inline_keyboard import Menu
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'^/c/\d+/s/:add/$') & custom_filters.admin_only,
)
async def add_source(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты добавляешь новый источник.\n\n'
        '**Введи публичное имя канала, частную ссылку, '
        'ID или перешли сообщение из него:**'
    )

    input_wait_manager.add(
        callback_query.message.chat.id, add_source_waiting_input, client, callback_query
    )


async def add_source_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data)

    #

    new_message = await message.reply_text('⏳ Проверка…')

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
                input_text = re.sub('https://t.me/', '', message.text)
                chat = await user.get_chat(input_text)
    except RPCError as e:
        await edit_text(f'❌ Что-то пошло не так\n\n{e}')
        return

    if chat.type != ChatType.CHANNEL:
        await edit_text('❌ Это не канал')
        return

    #

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        await edit_text(f'❌ Основной клиент не может подписаться на канал\n\n{e}')
        return

    category_id = menu.path.get_value('c')
    try:
        source_obj = Source.create(
            tg_id=chat.id, title=chat.title, category=category_id
        )
    except peewee.IntegrityError:
        await edit_text('❗️Этот канал уже используется')
        return

    Source.clear_actual_cache()

    category_obj: Category = Category.get(category_id)
    src_link = await get_channel_formatted_link(source_obj.tg_id)
    cat_link = await get_channel_formatted_link(category_obj.tg_id)
    success_text = f'✅ Источник **{src_link}** добавлен в категорию **{cat_link}**'
    await edit_text(success_text)

    await send_message_to_admins(client, callback_query, success_text)
