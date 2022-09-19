from pyrogram import Client, filters
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from initialization import logger
from models import Source, Filter, FILTER_CONTENT_TYPES
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager


@Client.on_callback_query(filters.regex(
    r'/s_\d+/$'))
async def list_type_content_filters(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    source_obj = Source.get_or_none(id=int(path.get_value('s')))

    inline_keyboard = []

    text = '**Общие фильтры**'
    if source_obj:
        text = (f'Источник: **{source_obj.title}**\n'
                f'Категория: **{source_obj.category.title}**')
        if custom_filters.is_admin(None, None, callback_query):
            inline_keyboard.append(
                [InlineKeyboardButton(
                    f'📝',
                    callback_data=path.add_action('edit')
                ), InlineKeyboardButton(
                    '✖️',
                    callback_data=path.add_action('delete')
                ), ],
            )

    inline_keyboard += buttons.get_list_model(
        data=FILTER_CONTENT_TYPES,
        path=path,
        prefix_path='t',
        counter_model=Filter,
        counter_filter_field_item='content_type',
        counter_filter_fields={
            'source': source_obj.id if source_obj else None, }
    )

    inline_keyboard += buttons.get_fixed(path)
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r'/t_\w+/$'))
async def list_filters(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    content_type = path.get_value('t')
    source_id = int(path.get_value('s'))
    source_obj = Source.get(id=source_id) if source_id else None

    select_kwargs = {
        'content_type': content_type,
        'source': source_obj.id if source_obj else None
    }

    inline_keyboard = []

    if custom_filters.is_admin(None, None, callback_query):
        inline_keyboard.append([InlineKeyboardButton(
            '➕ Добавить фильтр',
            callback_data=path.add_action('add')
        )])

    inline_keyboard += buttons.get_list_model(
        data=Filter,
        path=path,
        prefix_path='f',
        filter_kwargs=select_kwargs)

    inline_keyboard += buttons.get_fixed(path)

    text = '**Общие фильтры**'
    if source_obj:
        text = f'Канал: **{source_obj}**'

    await callback_query.message.edit_text(
        f'{text}\n'
        f'Фильтр: **{content_type}**',
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r'/f_\d+/$'))
async def detail_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_obj: Filter = Filter.get(id=int(path.get_value('f')))

    inline_keyboard = []

    if custom_filters.is_admin(None, None, callback_query):
        inline_keyboard.append([InlineKeyboardButton(
            f'📝',
            callback_data=path.add_action('edit')
        ), InlineKeyboardButton(
            '✖️',
            callback_data=path.add_action('delete')
        ), ], )

    inline_keyboard += buttons.get_fixed(path)

    text = (f'Канал: **{filter_obj.source}**'
            if filter_obj.source else '**Общий фильтр**')
    await callback_query.message.edit_text(
        f'{text}\n'
        f'Тип фильтра: **{filter_obj.content_type}**\n'
        f'Паттерн: `{filter_obj.pattern}`',
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r'/s_\d+/t_\w+/:add/$') & custom_filters.admin_only)
async def add_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    source_id = int(path.get_value('s'))
    source_obj = Source.get_or_none(id=source_id)
    content_type = path.get_value('t')

    text = 'ОК. Ты добавляешь '
    text += (f'фильтр для источника «{source_obj}» ' if source_obj
             else 'общий фильтр ')
    text += f'типа «{content_type}».\n\n**Введи паттерн нового фильтра:**'

    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, add_filter_wait_input, client, callback_query, content_type,
        source_obj)


async def add_filter_wait_input(_, message: Message, callback_query,
                                content_type, source_obj):
    logger.debug(callback_query.data)

    try:
        Filter.create(pattern=message.text, content_type=content_type,
                      source=source_obj.id if source_obj else None)

        text = '✅ Фильтр добавлен'
    except Exception as err:
        text = f'❌ Что-то пошло не так\n\n{err}'

    path = Path(callback_query.data)
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons.get_fixed(path, back_title='Фильтры'))
    )

    callback_query.data = path.get_prev()
    await list_filters(_, callback_query)


@Client.on_callback_query(filters.regex(
    r'/f_\d+/:edit/$') & custom_filters.admin_only)
async def edit_body_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    filter_id = int(path.get_value('f'))
    filter_obj = Filter.get_or_none(id=filter_id)

    text = 'ОК. Ты изменяешь '
    text += (f'фильтр для источника «{filter_obj.source.title}» '
             if filter_obj.source else 'общий фильтр ')
    text += (f'типа «{filter_obj.content_type}» с паттерном '
             f'«`{filter_obj.pattern}`».\n\n'
             f'**Введи новый паттерн фильтра:**')

    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, edit_body_filter_wait_input, client, callback_query,
        filter_obj)


async def edit_body_filter_wait_input(
        _, message: Message, callback_query: CallbackQuery, filter_obj):
    logger.debug(callback_query.data)

    try:
        filter_obj.pattern = message.text
        filter_obj.save()
        text = '✅ Фильтр изменен'
    except Exception as err:
        text = f'❌ При сохранении изменений произошла ошибка\n{err}'

    path = Path(callback_query.data)
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons.get_fixed(path, back_title='Параметры')
        )
    )

    callback_query.data = path.get_prev()
    await detail_filter(_, callback_query)


@Client.on_callback_query(filters.regex(
    r'f_\d+/:delete/') & custom_filters.admin_only)
async def delete_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_id = int(path.get_value('f'))

    if path.with_confirmation:
        q = (Filter
             .delete()
             .where(Filter.id == filter_id))
        q.execute()

        callback_query.data = path.get_prev(3)
        await list_filters(_, callback_query)
        return

    filter_obj = Filter.get(id=filter_id)

    text = (f'Канал: **{filter_obj.source}**\n'
            if filter_obj.source else '**Общий фильтр**\n')
    text += f'Тип фильтра: **{filter_obj.content_type}**\n'
    text += f'Паттерн: `{filter_obj.pattern}`\n\n'
    text += 'Ты **удаляешь** фильтр!'
    inline_keyboard = [[InlineKeyboardButton(
        '❌ Подтвердить удаление',
        callback_data=f'{path}/'
    ), ]]
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
