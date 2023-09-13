import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Message

from models import User
from plugins.bot.constants import CANCEL
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_user_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/a/:add/$') & custom_filters.admin_only,
)
async def add_admin(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты добавляешь нового администратора.\n\n'
        f'**Введи ID или имя пользователя** или {CANCEL}'
    )
    input_wait_manager.add(
        callback_query.message.chat.id,
        add_admin_waiting_input,
        client,
        callback_query,
    )


async def add_admin_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data)

    async def reply(t):
        await message.reply_text(
            text=t,
            reply_markup=menu.reply_markup,
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
        await reply('❗️Этот пользователь уже администратор')
        return

    adm_link = await get_user_formatted_link(admin_obj.id)
    text = f'✅ Администратор **{adm_link}** добавлен'
    await reply(text)

    await send_message_to_admins(client, callback_query, text)
