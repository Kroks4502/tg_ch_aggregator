import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            Message, InlineKeyboardButton)

from initialization import logger
from models import Category, Source
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_filter import list_category

SECTION = '^/c'


@Client.on_callback_query(filters.regex(r'^/(c|s)[\w/]*:(add|edit)/$'))
async def wait_input_category_channel(
        client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id

    if path.section == 'c':
        action = path.action
        text = 'ОК. Ты добавляешь новую категорию.\n\n'
        if action == 'edit':
            text = 'ОК. Ты меняешь канал у категории.\n\n'
        text += '**Введи ID канала или ссылку на него:**'
    else:
        text = ('ОК. Ты добавляешь новый источник.\n\n'
                '**Введи ID канала или ссылку на него:**')
    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, add_edit, client, callback_query)


async def add_edit(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    reply_markup_fix_buttons = InlineKeyboardMarkup(
        buttons.get_fixed(path, back_title='Назад'))

    input_text = re.sub('https://t.me/', '', message.text)

    try:
        channel = await client.get_chat(input_text)
    except (exceptions.bad_request_400.UsernameInvalid,
            exceptions.bad_request_400.UsernameNotOccupied):
        await message.reply_text(
            '❌ Объект не найден',
            reply_markup=reply_markup_fix_buttons)
        return

    if channel.type != ChatType.CHANNEL:
        await message.reply_text(
            '❌ Это не канал',
            reply_markup=reply_markup_fix_buttons)
        return

    section = path.section
    if section == 'c':
        try:
            member = await channel.get_member(client.me.id)
        except exceptions.bad_request_400.UserNotParticipant:
            await message.reply_text(
                '❌ Бот не подписан на этот канал',
                reply_markup=reply_markup_fix_buttons)
            return

        if not member.privileges.can_post_messages:
            await message.reply_text(
                '❌ Бот не имеет прав на публикацию сообщений',
                reply_markup=reply_markup_fix_buttons)
            return

    action = path.action
    try:
        if section == 'c':
            if action == 'add':
                Category.create(tg_id=channel.id, title=channel.title)
                success_text = f'✅ Категория «{channel.title}» добавлена'
            else:
                category_id = int(path.get_value('c'))
                category = Category.get(id=category_id)
                success_text = (f'✅ Категория «{category.title}» изменена ' 
                                f'на «{channel.title}»')
                category.tg_id = channel.id
                category.title = channel.title
                category.save()
        else:
            category_id = int(path.get_value('c'))
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
    await list_category(client, callback_query)


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*/c_\d+/$'))
async def detail(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    category_id = int(path.get_value('c'))
    category_obj: Category = Category.get(id=category_id)

    inline_keyboard = (
            [
                [InlineKeyboardButton(
                    f'Канал: {category_obj.title}',
                    callback_data=path.add_action('edit')
                ), ],
                [InlineKeyboardButton(
                    '✖️ Удалить категорию',
                    callback_data=path.add_action('delete')
                ), ],
            ]
            + buttons.get_fixed(path)
    )

    await callback_query.message.edit_text(
        f'Категория: {category_obj.title}\n\n'
        f'{path}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*:delete/'))
async def delete(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj: Category = Category.get_or_none(id=category_id)

    if path.with_confirmation:
        callback_query.data = path.get_prev(3)
        category_obj.delete_instance()
        await list_category(_, callback_query)
        return
    await callback_query.message.edit_text(
        f'Категория: {category_obj.title}\n\n'
        f'{path}',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        '❌ Подтвердить удаление',
                        callback_data=f'{path}/'
                    ),
                ],
            ]
            + buttons.get_fixed(path))
    )
