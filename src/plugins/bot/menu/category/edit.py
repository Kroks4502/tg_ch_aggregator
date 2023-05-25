import logging
import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError, exceptions
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from clients import user
from models import Category
from plugins.bot.menu.main import set_main_menu
from plugins.bot.menu.section_source import list_source

from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'^/c_\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_category(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты меняешь канал для категории, '
        'в который будут пересылаться сообщения из источников. '
        'Этот бот должен быть администратором канала '
        'с возможностью публиковать записи.\n\n'
        '**Введи публичное имя канала или ссылку на канал:**'
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_category_waiting_input,
        client,
        callback_query,
    )


async def edit_category_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    logging.debug(callback_query.data)

    input_text = re.sub('https://t.me/', '', message.text)
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
        chat = await user.get_chat(input_text)
    except RPCError as e:
        await reply(f'❌ Что-то пошло не так\n\n{e}')
        return

    if chat.type != ChatType.CHANNEL:
        await reply('❌ Это не канал')
        return

    try:
        member = await chat.get_member(client.me.id)
        if not member.privileges.can_post_messages:
            await reply('❌ Бот не имеет прав на публикацию в этом канале')
            return
    except exceptions.bad_request_400.UserNotParticipant:
        await reply('❌ Бот не администратор этого канала')
        return

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        await reply(f'❌ Основной клиент не может подписаться на канал\n\n{e}')
        return

    try:
        category_id = int(path.get_value('c'))
        q = Category.update(
            {Category.tg_id: chat.id, Category.title: chat.title}
        ).where(Category.id == category_id)
        q.execute()
        success_text = f'✅ Категория {category_id} изменена на **{chat.title}**'
        Category.clear_actual_cache()
    except peewee.IntegrityError:
        await reply('❗️Этот канал уже используется')
        return

    await reply(success_text)

    await send_message_to_admins(client, callback_query, success_text)

    callback_query.data = path.get_prev()
    if path.action == 'add':
        await set_main_menu(client, callback_query, needs_an_answer=False)
        return
    await list_source(client, callback_query, needs_an_answer=False)
