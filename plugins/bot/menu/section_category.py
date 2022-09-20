import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from initialization import logger
from models import Source, Category
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_source import list_source


@Client.on_callback_query(filters.regex(
    r'^/$|s_\d+/:edit/$'))
async def list_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    action = path.action

    text = '**Агрегатор каналов**'
    if action == 'edit':
        source_id = int(path.get_value('s'))
        source_obj = Source.get(id=source_id)
        text = (f'Источник: **{source_obj}**\n\n'
                f'Ты **меняешь категорию** у источника.\n'
                f'Выбери новую категорию:')

    inline_keyboard = []

    button_show_all_title = ''
    if action != 'edit':
        button_show_all_title = f'📚 Все источники'
        if custom_filters.is_admin(None, None, callback_query):
            inline_keyboard.append([InlineKeyboardButton(
                '➕ Добавить категорию',
                callback_data=path.add_action('add')
            ), ])

    query = (Category
             .select(Category.id,
                     Category.title,
                     peewee.fn.Count(Source.id).alias('count'))
             .join(Source, peewee.JOIN.LEFT_OUTER)
             .group_by(Category.id))

    inline_keyboard += buttons.get_list_model(
        data={f'{item.id}': (item.title, item.count) for item in query},
        path=path,
        prefix_path='c',
        button_show_all_title=button_show_all_title,
    )

    if action != 'edit':
        inline_keyboard.append([InlineKeyboardButton(
            f'🔘 Общие фильтры',
            callback_data=path.add_value('s', 0)
        )])

    if action == 'edit':
        inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r'^/:add/$|^/c_\d+/:edit/$') & custom_filters.admin_only)
async def add_edit_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id

    text = 'ОК. Ты меняешь канал у категории.\n\n'
    if path.action == 'add':
        text = 'ОК. Ты добавляешь новую категорию.\n\n'
    text += '**Введи ID канала или ссылку на него:**'

    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, add_edit_category_waiting_input, client, callback_query)


async def add_edit_category_waiting_input(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    input_text = re.sub('https://t.me/', '', message.text)

    path = Path(callback_query.data)
    reply_markup_fix_buttons = InlineKeyboardMarkup(
        buttons.get_fixed(path, back_title='Назад'))

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

    try:
        member = await channel.get_member(client.me.id)
    except exceptions.bad_request_400.UserNotParticipant:
        await message.reply_text(
            '❌ Бот не администратор этого канала',
            reply_markup=reply_markup_fix_buttons)
        return

    if not member.privileges.can_post_messages:
        await message.reply_text(
            '❌ Бот не имеет прав на публикацию сообщений в этом канале',
            reply_markup=reply_markup_fix_buttons)
        return

    try:
        if path.action == 'add':
            Category.create(tg_id=channel.id, title=channel.title)
            success_text = f'✅ Категория «{channel.title}» добавлена'

        else:
            category_id = int(path.get_value('c'))
            category = Category.get(id=category_id)
            category.tg_id = channel.id
            old_title = category.title
            category.title = channel.title
            category.save()
            success_text = (f'✅ Категория «{old_title}» изменена '
                            f'на «{channel.title}»')

    except peewee.IntegrityError:
        await message.reply_text(
            f'❗️Этот канал уже используется',
            reply_markup=reply_markup_fix_buttons)
        return

    await message.reply_text(
        success_text,
        reply_markup=reply_markup_fix_buttons)

    callback_query.data = path.get_prev()
    if path.action == 'add':
        await list_category(client, callback_query)
        return
    await list_source(client, callback_query)


@Client.on_callback_query(filters.regex(
    r'c_\d+/:delete/') & custom_filters.admin_only)
async def delete_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))

    if path.with_confirmation:
        q = (Category
             .delete()
             .where(Category.id == category_id))
        q.execute()

        callback_query.data = path.get_prev(3)
        await list_category(_, callback_query)
        return

    category_obj = Category.get(id=category_id)
    text = f'Категория: **{category_obj.title}**\n\n'
    text += 'Ты **удаляешь** категорию!'

    inline_keyboard = [[InlineKeyboardButton(
        '❌ Подтвердить удаление',
        callback_data=f'{path}/'
    ), ]]
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
