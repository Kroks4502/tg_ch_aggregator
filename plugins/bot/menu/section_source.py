import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from initialization import logger, user
from models import Source, Filter, Category
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_filter import list_type_content_filters


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/$'))
async def list_source(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj = Category.get(id=category_id) if category_id else None

    text = (f'Категория: **{category_obj}**'
            if category_obj else '**Все источники**')

    inline_keyboard = []

    if category_obj and custom_filters.is_admin(None, None, callback_query):
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

    select_kwargs = None
    if category_obj:
        select_kwargs = {'category': category_obj.id}
    inline_keyboard += buttons.get_list_model(
        data=Source,
        path=path,
        prefix_path='s',
        filter_kwargs=select_kwargs,
        counter_model=Filter,
        counter_filter_fields_with_data_attr={'source': 'id'}
    )

    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r's_\d+/:edit/c_\d+/$') & custom_filters.admin_only)
async def edit_source_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))
    new_category_id = int(path.get_value('c', after_action=True))

    q = (Source
         .update({Source.category: new_category_id})
         .where(Source.id == source_id))
    q.execute()

    callback_query.data = path.get_prev(2)
    await list_type_content_filters(_, callback_query)


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/:add/$') & custom_filters.admin_only)
async def add_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    chat_id = callback_query.message.chat.id

    text = ('ОК. Ты добавляешь новый источник.\n\n'
            '**Введи ID канала или ссылку на него:**')

    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, wait_input_source_channel, client, callback_query)


async def wait_input_source_channel(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))

    reply_markup_fix_buttons = InlineKeyboardMarkup(
        buttons.get_fixed(path, back_title='Назад'))

    input_text = re.sub('https://t.me/', '', message.text)

    try:
        channel = await client.get_chat(input_text)
    except (exceptions.BadRequest, exceptions.NotAcceptable) as err:
        await message.reply_text(
            f'❌ Что-то пошло не так\n\n{err}',
            reply_markup=reply_markup_fix_buttons)
        return

    if channel.type != ChatType.CHANNEL:
        await message.reply_text(
            '❌ Это не канал',
            reply_markup=reply_markup_fix_buttons)
        return

    if channel.id not in [dialog.chat.id
                          async for dialog in user.get_dialogs()]:
        await message.reply_text(
            '❌ Клиент не подписан на этот канал',
            reply_markup=reply_markup_fix_buttons)
        return

    try:
        Source.create(tg_id=channel.id, title=channel.title,
                      category=category_id)
        success_text = f'✅ Источник «{channel.title}» добавлен'

    except peewee.IntegrityError:
        await message.reply_text(
            f'❗️Этот канал уже используется',
            reply_markup=reply_markup_fix_buttons)
        return

    await message.reply_text(
        success_text,
        reply_markup=reply_markup_fix_buttons)

    callback_query.data = path.get_prev()
    await list_source(client, callback_query)


@Client.on_callback_query(filters.regex(
    r's_\d+/:delete/') & custom_filters.admin_only)
async def delete_source(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))

    if path.with_confirmation:
        q = (Source
             .delete()
             .where(Source.id == source_id))
        q.execute()

        callback_query.data = path.get_prev(3)
        await list_source(_, callback_query)
        return

    source_obj = Source.get(id=source_id)
    text = f'Источник: **{source_obj.title}**\n\n'
    text += 'Ты **удаляешь** источник!'

    inline_keyboard = [[InlineKeyboardButton(
        '❌ Подтвердить удаление',
        callback_data=f'{path}/'
    ), ]]
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
