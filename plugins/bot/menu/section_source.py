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
from plugins.bot.menu.helpers.senders import send_message_to_main_user
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_filter import list_type_content_filters


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/$'))
async def list_source(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj: Category = (Category.get(id=category_id)
                              if category_id else None)

    text = (f'Категория: **{await category_obj.get_formatted_link()}**'
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
    source_obj: Source = Source.get(id=source_id)

    q = (Source
         .update({Source.category: int(path.get_value('c', after_action=True))})
         .where(Source.id == source_id))
    q.execute()
    Source.clear_actual_cache()

    callback_query.data = path.get_prev(2)
    await callback_query.answer('Категория изменена')
    await list_type_content_filters(client, callback_query)

    await send_message_to_main_user(
        client, callback_query,
        f'Изменена категория у источника '
        f'{await source_obj.get_formatted_link()} '
        f'на {await source_obj.category.get_formatted_link()}')


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/:add/$') & custom_filters.admin_only)
async def add_source(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    text = ('ОК. Ты добавляешь новый источник.\n\n'
            '**Введи ID канала или ссылку на него:**')

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

    async def reply(text):
        await new_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Назад')),
            disable_web_page_preview=True)

    try:
        chat = await client.get_chat(input_text)
    except (exceptions.BadRequest, exceptions.NotAcceptable) as err:
        await reply(f'❌ Что-то пошло не так\n\n{err}')
        return

    if chat.type != ChatType.CHANNEL:
        await reply('❌ Это не канал')
        return

    if chat.id not in [dialog.chat.id
                       async for dialog in user.get_dialogs()]:
        await reply('❌ Клиент не подписан на этот канал')
        return

    try:
        Source.create(tg_id=chat.id, title=chat.title,
                      category=category_id)
        Source.clear_actual_cache()
    except peewee.IntegrityError:
        await reply(f'❗️Этот канал уже используется')
        return

    category_obj: Category = Category.get(id=category_id)
    success_text = (f'✅ Источник [{chat.title}](https://{chat.username}.t.me) '
                    f'добавлен в категорию '
                    f'{await category_obj.get_formatted_link()}')
    await reply(success_text)

    callback_query.data = path.get_prev()
    await list_source(client, callback_query)

    await send_message_to_main_user(client, callback_query, success_text)


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

        await send_message_to_main_user(
            client, callback_query,
            f'Удален источник **{await source_obj.get_formatted_link()}**')
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        f'Источник: **{await source_obj.get_formatted_link()}**\n\n'
        'Ты **удаляешь** источник!',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            '❌ Подтвердить удаление',
            callback_data=f'{path}/'
        ), ]] + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )
