import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from log import logger
from initialization import user
from models import Source, Filter, Category
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_filter import list_type_content_filters


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/$'))
async def list_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj = Category.get(id=category_id) if category_id else None
    category_chat = await client.get_chat(category_obj.tg_id)
    text = (f'Категория: **[{category_obj}]({category_chat.invite_link})**'
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
    )

    inline_keyboard += buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
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

    Source.clear_actual_cache()

    callback_query.data = path.get_prev(2)
    await callback_query.answer()
    await list_type_content_filters(_, callback_query)


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/:add/$') & custom_filters.admin_only)
async def add_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    chat_id = callback_query.message.chat.id

    text = ('ОК. Ты добавляешь новый источник.\n\n'
            '**Введи ID канала или ссылку на него:**')

    await callback_query.answer()
    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, add_source_waiting_input, client, callback_query)


async def add_source_waiting_input(
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

        Source.clear_actual_cache()

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
async def delete_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id)
    source_chat = await user.get_chat(source_obj.tg_id)
    if path.with_confirmation:
        source_obj.delete_instance()
        Source.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Источник удален')
        await list_source(client, callback_query)

        if callback_query.from_user.id != user.me.id:
            await client.send_message(
                user.me.id, f'@{callback_query.from_user.username} '
                            f'удалил источник [{source_obj.title}]'
                            f'(https://{source_chat.username}.t.me)',
                disable_web_page_preview=True)
        return

    text = (f'Источник: **[{source_obj.title}]'
            f'(https://{source_chat.username}.t.me)**\n\n')
    text += 'Ты **удаляешь** источник!'

    inline_keyboard = [[InlineKeyboardButton(
        '❌ Подтвердить удаление',
        callback_data=f'{path}/'
    ), ]]
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
    )
