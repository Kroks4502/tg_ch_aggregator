import peewee
from pyrogram import Client, filters
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from log import logger
from models import Source, Filter, FILTER_CONTENT_TYPES
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.helpers.senders import send_message_to_admins
from plugins.bot.menu.managers.input_wait import input_wait_manager


@Client.on_callback_query(filters.regex(
    r'/s_\d+/$'))
async def list_type_content_filters(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get_or_none(id=source_id)

    text = '**Общие фильтры**'
    inline_keyboard = []
    if source_obj:
        text = (f'Источник: **{await source_obj.get_formatted_link()}**'
                f'\nКатегория: '
                f'**{await source_obj.category.get_formatted_link()}**')
        if is_admin(callback_query.from_user.id):
            inline_keyboard.append(
                [InlineKeyboardButton(
                    f'📝',
                    callback_data=path.add_action('edit')
                ), InlineKeyboardButton(
                    '✖️',
                    callback_data=path.add_action('delete')
                ), ],
            )

    source_where = None if source_id else Filter.source.is_null(True)
    query = (
        Filter
        .select(Filter.content_type,
                peewee.fn.Count(Filter.id).alias('count'))
        .where(source_where if source_where else Filter.source == source_id)
        .group_by(Filter.content_type)
    )
    data = {content_type: (content_type, 0)
            for content_type in FILTER_CONTENT_TYPES}
    data.update({item.content_type: (item.content_type, item.count)
                 for item in query})
    inline_keyboard += buttons.get_list_model(
        data=data,
        path=path,
        prefix_path='t',
    )

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(
    r'/t_\w+/$'))
async def list_filters(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    content_type = path.get_value('t')
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id) if source_id else None

    if source_obj:
        text = f'Источник: **{await source_obj.get_formatted_link()}**'
    else:
        text = '**Общие фильтры**'
    text += f'\nФильтр: **{content_type}**'

    inline_keyboard = []
    if is_admin(callback_query.from_user.id):
        inline_keyboard.append([InlineKeyboardButton(
            '➕ Добавить фильтр',
            callback_data=path.add_action('add')
        )])

    source_where = None if source_id else Filter.source.is_null(True)
    query = (
        Filter
        .select()
        .where((source_where if source_where else Filter.source == source_id)
               & (Filter.content_type == content_type))
    )
    inline_keyboard += buttons.get_list_model(
        data={f'{item.id}': (item.pattern, 0) for item in query},
        path=path,
        prefix_path='f')

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(
    r'/f_\d+/$'))
async def detail_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_obj: Filter = Filter.get(id=int(path.get_value('f')))

    inline_keyboard = []
    if is_admin(callback_query.from_user.id):
        inline_keyboard.append([InlineKeyboardButton(
            f'📝',
            callback_data=path.add_action('edit')
        ), InlineKeyboardButton(
            '✖️',
            callback_data=path.add_action('delete')
        ), ], )
    inline_keyboard += buttons.get_fixed(path)

    if filter_obj.source:
        text = f'Источник: **{await filter_obj.source.get_formatted_link()}**'
    else:
        text = '**Общий фильтр**'
    text += (f'\nТип фильтра: **{filter_obj.content_type}**'
             f'\nПаттерн: `{filter_obj.pattern}`')

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(
    r'/s_\d+/t_\w+/:add/$') & custom_filters.admin_only)
async def add_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get_or_none(id=source_id)
    content_type = path.get_value('t')

    text = 'ОК. Ты добавляешь '
    text += (f'фильтр для источника {await source_obj.get_formatted_link()} '
             if source_obj else 'общий фильтр ')
    text += (f'типа **{content_type}**. Паттерн является регулярным выражением '
             f'с игнорированием регистра.\n\n'
             '**Введи паттерн нового фильтра:**')

    await callback_query.answer()
    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        chat_id, add_filter_waiting_input, client, callback_query,
        content_type, source_obj)


async def add_filter_waiting_input(
        client: Client, message: Message, callback_query,
        content_type, source_obj):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Параметры')),
            disable_web_page_preview=True)

    filter_obj = Filter.create(
        pattern=message.text, content_type=content_type,
        source=source_obj.id if source_obj else None)
    Filter.clear_actual_cache()

    if source_obj:
        success_text = (f'✅ Фильтр для источника '
                        f'{await filter_obj.source.get_formatted_link()} ')
    else:
        success_text = '✅ Общий фильтр '
    success_text += (f'типа **{filter_obj.content_type}** '
                     f'с паттерном `{filter_obj.pattern}` добавлен')

    await reply(success_text)

    callback_query.data = path.get_prev()
    await list_filters(client, callback_query)

    await send_message_to_admins(client, callback_query, success_text)


@Client.on_callback_query(filters.regex(
    r'/f_\d+/:edit/$') & custom_filters.admin_only)
async def edit_body_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get_or_none(id=filter_id)

    text = 'ОК. Ты изменяешь '
    text += (f'фильтр для источника '
             f'{await filter_obj.source.get_formatted_link()} '
             if filter_obj.source else 'общий фильтр ')
    text += (f'типа **{filter_obj.content_type}** с паттерном '
             f'`{filter_obj.pattern}`.\n\n'
             f'**Введи новый паттерн фильтра:**')

    await callback_query.answer()
    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        chat_id, edit_body_filter_wait_input, client, callback_query,
        filter_obj)


async def edit_body_filter_wait_input(
        client: Client, message: Message, callback_query: CallbackQuery,
        filter_obj: Filter):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Параметры')),
            disable_web_page_preview=True)

    filter_obj.pattern = message.text
    filter_obj.save()
    Filter.clear_actual_cache()

    if filter_obj.source:
        success_text = (f'✅ Фильтр для источника '
                        f'{await filter_obj.source.get_formatted_link()} ')
    else:
        success_text = '✅ Общий фильтр '
    success_text += (f'типа **{filter_obj.content_type}** '
                     f'с паттерном `{filter_obj.pattern}` изменен')

    await reply(success_text)

    callback_query.data = path.get_prev()
    await detail_filter(client, callback_query)

    await send_message_to_admins(client, callback_query, success_text)


@Client.on_callback_query(filters.regex(
    r'f_\d+/:delete/') & custom_filters.admin_only)
async def delete_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get(id=filter_id)
    if filter_obj.source:
        text = f'Источник: **{await filter_obj.source.get_formatted_link()}**'
    else:
        text = '**Общий фильтр**'
    text += (f'\nТип фильтра: **{filter_obj.content_type}**'
             f'\nПаттерн: `{filter_obj.pattern}`')

    if path.with_confirmation:
        q = (Filter
             .delete()
             .where(Filter.id == filter_id))
        q.execute()

        Filter.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Паттерн удален')
        await list_filters(client, callback_query)

        await send_message_to_admins(
            client, callback_query, f'Удален фильтр:\n{text}')
        return

    text += '\n\nТы **удаляешь** фильтр!'

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            '❌ Подтвердить удаление',
            callback_data=f'{path}/'
        ), ]] + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )
