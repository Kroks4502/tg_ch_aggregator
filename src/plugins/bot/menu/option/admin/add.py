import logging

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from models import Admin
from plugins.bot.menu.option.admin.list import list_admins

from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_user_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'^/o/a/:add/$') & custom_filters.admin_only,
)
async def add_admin(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    chat_id = callback_query.message.chat.id

    text = (
        'ОК. Ты добавляешь нового администратора.\n\n**Введи ID или имя пользователя:**'
    )

    await callback_query.answer()
    await callback_query.message.reply(text)
    input_wait_manager.add(chat_id, add_admin_waiting_input, client, callback_query)


async def add_admin_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_footer(path, back_title='Назад')
            ),
            disable_web_page_preview=True,
        )

    try:
        chat = await client.get_chat(message.text)
    except RPCError as e:
        await reply(f'❌ Что-то пошло не так\n\n{e}')
        return

    if chat.type != ChatType.PRIVATE:
        await reply('❌ Это не пользователь')
        return

    try:
        if chat.username:
            username = chat.username
        else:
            username = (
                f'{chat.first_name + " " if chat.first_name else ""}'
                f'{chat.last_name + " " if chat.last_name else ""}'
            )
        admin_obj = Admin.create(tg_id=chat.id, username=username)
        Admin.clear_actual_cache()
    except peewee.IntegrityError:
        await reply(f'❗️Этот пользователь уже администратор')
        return

    success_text = (
        '✅ Администратор '
        f'**{await get_user_formatted_link(admin_obj.tg_id)}** добавлен'
    )
    await reply(success_text)

    callback_query.data = path.get_prev()
    await list_admins(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)
    return
