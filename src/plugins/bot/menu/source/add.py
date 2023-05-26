import logging
import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from clients import user
from models import Source, Category
from plugins.bot.menu.source.list import list_source
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'^/c_\d+/:add/$') & custom_filters.admin_only,
)
async def add_source(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    text = (
        'ОК. Ты добавляешь новый источник.\n\n'
        '**Введи публичный username канала, ссылку на него '
        'или перешли мне пост из этого канала:**'
    )

    await callback_query.answer()
    await callback_query.message.reply(text)
    input_wait_manager.add(
        callback_query.message.chat.id, add_source_waiting_input, client, callback_query
    )


async def add_source_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))

    input_text = re.sub('https://t.me/', '', message.text)

    new_message = await message.reply_text('⏳ Проверка…')

    async def edit_text(text):
        await new_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_footer(path, back_title='Назад')
            ),
            disable_web_page_preview=True,
        )

    try:
        if message.forward_from_chat:
            chat = message.forward_from_chat
        else:
            chat = await user.get_chat(input_text)
    except RPCError as e:
        await edit_text(f'❌ Что-то пошло не так\n\n{e}')
        return

    if chat.type != ChatType.CHANNEL:
        await edit_text('❌ Это не канал')
        return

    try:
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        await edit_text(f'❌ Основной клиент не может подписаться на канал\n\n{e}')
        return

    try:
        Source.create(tg_id=chat.id, title=chat.title, category=category_id)
        Source.clear_actual_cache()
    except peewee.IntegrityError:
        await edit_text(f'❗️Этот канал уже используется')
        return

    category_obj: Category = Category.get(id=category_id)
    success_text = (
        f'✅ Источник [{chat.title}](https://{chat.username}.t.me) '
        'добавлен в категорию '
        f'{await get_channel_formatted_link(category_obj.tg_id)}'
    )
    await edit_text(success_text)

    callback_query.data = path.get_prev()
    await list_source(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)
