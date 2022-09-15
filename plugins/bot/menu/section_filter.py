from pyrogram import Client, filters
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)

from initialization import logger
from models import Category, Source, Filter, FILTER_CONTENT_TYPES
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.managers.input_wait import input_wait_manager

SECTION = '^/f'


@Client.on_callback_query(filters.regex(
    r'^/(c|s|f)(/|[\w/]*/f_\d+/:edit_s/|/[\w/]*s_\d+/:edit_c/)$'))
async def list_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    button_show_all_title = '📚 Все источники'
    inline_keyboard = []
    section = path.section
    action = path.action

    if section == 'f':
        if not action:
            inline_keyboard.append([InlineKeyboardButton(
                '🔘 Общие фильтры', callback_data=path.add_value('s', 0))])
        elif action == 'edit_s':
            inline_keyboard.append([InlineKeyboardButton(
                '✖️ Без источника', callback_data=f'{path}c_0/s_0/')])
    elif section == 'c':
        button_show_all_title = ''
        inline_keyboard.append([InlineKeyboardButton(
            '➕ Добавить категорию',
            callback_data=path.add_action('add')
        ), ])

    inline_keyboard = buttons.get_list_model(
        data=Category,
        path=path,
        prefix_path='c',
        button_show_all_title=button_show_all_title
    ) + inline_keyboard

    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        str(path),
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    r'^/((s|f)|f/[\w/]*/f_\d+/:edit_s)/c_\d+/$'))
async def list_channel(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c', after_action=True))
    select_kwargs = None
    if category_id:
        select_kwargs = {'category': category_id}
    inline_keyboard = buttons.get_list_model(
        data=Source,
        path=path,
        prefix_path='s',
        select_kwargs=select_kwargs
    )
    if path.section == 's' and path.get_value('c') != '0':
        inline_keyboard.append([InlineKeyboardButton(
            '➕ Добавить источник',
            callback_data=path.add_action('add')
        ), ])
    inline_keyboard += buttons.get_fixed(path)
    await callback_query.message.edit_text(
        str(path),
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(
    filters.regex(SECTION + r'(/[\w/]*s_\d+/|[\w/]*/f_\d+/:edit_t/)$'))
async def list_filter_content_type(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    inline_keyboard = buttons.get_list_model(
        data=FILTER_CONTENT_TYPES,
        path=path,
        prefix_path='t'
    ) + buttons.get_fixed(path)
    await callback_query.message.edit_text(
        str(path),
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(SECTION + r'/[\w/]*/t_\w+/$'))
async def list_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    content_type = path.get_value('t')
    channel_id = int(path.get_value('s'))
    select_kwargs = {
        'content_type': content_type,
        'source': channel_id if channel_id else None
    }

    inline_keyboard = buttons.get_list_model(
        data=Filter,
        path=path,
        prefix_path='f',
        select_kwargs=select_kwargs)
    inline_keyboard.append([
        InlineKeyboardButton(
            '➕ Добавить фильтр',
            callback_data=path.add_action('add'))])
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.message.edit_text(
        str(path),
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*/f_\d+/$'))
async def detail_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get(id=filter_id)

    inline_keyboard = (
            [
                [InlineKeyboardButton(
                    f'Паттерн: {filter_obj.pattern}',
                    callback_data=path.add_action('edit_p')
                ), ],
                [InlineKeyboardButton(
                    f'Тип контента: {filter_obj.content_type}',
                    callback_data=path.add_action('edit_t')
                ), ],
                [InlineKeyboardButton(
                    f'Источник: {filter_obj.source.title if filter_obj.source else "не установлен"}',
                    callback_data=path.add_action('edit_s')
                ), ],
                [InlineKeyboardButton(
                    '✖️ Удалить фильтр',
                    callback_data=path.add_action('delete')
                ), ],
            ]
            + buttons.get_fixed(path)
    )

    await callback_query.message.edit_text(
        f'`{filter_obj.pattern}`\n\n{path}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(SECTION + r'/[\w/]*/:add/$'))
async def add_filter(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    channel_id = int(path.get_value('s'))
    channel_obj = Source.get_or_none(id=channel_id)
    content_type = path.get_value('t')

    text = 'ОК. Ты добавляешь '
    text += (f'фильтр для источника «{channel_obj}» ' if channel_obj
             else 'общий фильтр ')
    text += f'типа «{content_type}».\n\n**Введи паттерн нового фильтра:**'

    await client.send_message(chat_id, text)
    input_wait_manager.add(
        chat_id, add_filter_wait_input, client, callback_query, content_type,
        channel_obj)


async def add_filter_wait_input(_, message: Message, callback_query,
                                content_type, channel_obj):
    logger.debug(callback_query.data)

    try:
        Filter.create(pattern=message.text, content_type=content_type,
                      source=channel_obj.id if channel_obj else None)

        text = '✅ Фильтр добавлен'
    except Exception as err:
        text = f'❌ При добавлении произошла ошибка\n{err}'

    path = Path(callback_query.data)
    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons.get_fixed(path, back_title='Фильтры'))
    )

    callback_query.data = path.get_prev()
    await list_filter(_, callback_query)


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*/f_\d+/:edit_p/$'))
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


@Client.on_callback_query(
    filters.regex(SECTION + r'[\w/]*/f_\d+/:edit_t/t_\w+/$'))
async def edit_type_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    content_type = path.get_value('t', after_action=True)
    filter_id = int(path.get_value('f'))
    filter_obj = Filter.get_or_none(id=filter_id)
    filter_obj.content_type = content_type
    filter_obj.save()

    callback_query.data = path.get_prev(2)
    await detail_filter(_, callback_query)


@Client.on_callback_query(
    filters.regex(SECTION + r'[\w/]*/f_\d+/:edit_s/\w+/s_\d+/$'))
async def edit_channel_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    channel_id = int(path.get_value('s', after_action=True))

    filter_id = int(path.get_value('f'))
    filter_obj = Filter.get_or_none(id=filter_id)
    filter_obj.source = channel_id if channel_id > 0 else None
    filter_obj.save()

    callback_query.data = path.get_prev(3)
    await detail_filter(_, callback_query)


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*f_\d+/:delete/'))
async def delete_filter(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get(id=filter_id)

    if path.with_confirmation:
        callback_query.data = path.get_prev(3)
        filter_obj.delete_instance()
        await list_filter(_, callback_query)
        return
    await callback_query.message.edit_text(
        str(path),
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
