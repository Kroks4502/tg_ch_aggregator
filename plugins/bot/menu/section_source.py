import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from log import logger
from initialization import user
from models import Source, Filter, Category
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.links import get_channel_formatted_link
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.helpers.senders import send_message_to_admins
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_filter import list_types_filters


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/$'))
async def list_source(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj: Category = (Category.get(id=category_id)
                              if category_id else None)

    text = (f'Категория: **{await get_channel_formatted_link(category_obj.tg_id)}**'
            if category_obj else '**Все источники**')

    inline_keyboard = []
    if category_obj and is_admin(callback_query.from_user.id):
        inline_keyboard.append([InlineKeyboardButton(
            '➕',
            callback_data=path.add_action('add')
        ), InlineKeyboardButton(
            f'📝',
            callback_data=path.add_action('edit')
        ), InlineKeyboardButton(
            '✖️',
            callback_data=path.add_action('delete')
        ), ])
    query = (
        Source
        .select(Source.id, Source.title,
                peewee.fn.Count(Filter.id).alias('count'))
        .where(Source.category == category_id if category_id else True)
        .join(Filter, peewee.JOIN.LEFT_OUTER)
        .group_by(Source.id)
    )
    inline_keyboard += buttons.get_list_model(
        data={item.id: (item.title, item.count) for item in query},
        path=path,
        prefix_path='s',
    ) + buttons.get_fixed(path)

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(
    r's_\d+/:edit/c_\d+/$') & custom_filters.admin_only)
async def edit_source_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))
    category_obj: Category = Category.get(id=int(path.get_value('c', after_action=True)))
    source_obj: Source = Source.get(id=source_id)

    q = (Source
         .update({Source.category: category_obj})
         .where(Source.id == source_id))
    q.execute()
    Source.clear_actual_cache()

    callback_query.data = path.get_prev(2)
    await callback_query.answer('Категория изменена')
    await list_types_filters(client, callback_query)

    await send_message_to_admins(
        client, callback_query,
        f'Изменена категория у источника '
        f'{await get_channel_formatted_link(source_obj.tg_id)} '
        f'на {await get_channel_formatted_link(category_obj.tg_id)}')


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/:add/$') & custom_filters.admin_only)
async def add_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    text = ('ОК. Ты добавляешь новый источник.\n\n'
            '**Введи публичный username канала, ссылку на него '
            'или перешли мне пост из этого канала:**')

    await callback_query.answer()
    await callback_query.message.reply(text)
    input_wait_manager.add(
        callback_query.message.chat.id, add_source_waiting_input, client,
        callback_query)


async def add_source_waiting_input(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))

    input_text = re.sub('https://t.me/', '', message.text)

    new_message = await message.reply_text('⏳ Проверка…')

    async def edit_text(text):
        await new_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Назад')),
            disable_web_page_preview=True)

    try:
        if message.forward_date:
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
        await edit_text(f'❌ Основной клиент не может подписаться на канал\n\n'
                        f'{e}')
        return

    try:
        Source.create(tg_id=chat.id, title=chat.title,
                      category=category_id)
        Source.clear_actual_cache()
    except peewee.IntegrityError:
        await edit_text(f'❗️Этот канал уже используется')
        return

    category_obj: Category = Category.get(id=category_id)
    success_text = (f'✅ Источник [{chat.title}](https://{chat.username}.t.me) '
                    f'добавлен в категорию '
                    f'{await get_channel_formatted_link(category_obj.tg_id)}')
    await edit_text(success_text)

    callback_query.data = path.get_prev()
    await list_source(client, callback_query)

    await send_message_to_admins(client, callback_query, success_text)


@Client.on_callback_query(filters.regex(
    r's_\d+/:delete/') & custom_filters.admin_only)
async def delete_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_obj: Source = Source.get(id=int(path.get_value('s')))
    if path.with_confirmation:
        source_obj.delete_instance()
        Source.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Источник удален')
        await list_source(client, callback_query)

        await send_message_to_admins(
            client, callback_query,
            f'❌ Удален источник **{await get_channel_formatted_link(source_obj.tg_id)}**')
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        f'Источник: **{await get_channel_formatted_link(source_obj.tg_id)}**\n\n'
        'Ты **удаляешь** источник!',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            '❌ Подтвердить удаление',
            callback_data=f'{path}/'
        ), ]] + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )
