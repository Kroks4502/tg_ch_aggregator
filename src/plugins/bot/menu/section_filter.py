import logging

import peewee
from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from filter_types import (
    FILTER_ENTITY_TYPES_BY_ID,
    FILTER_MESSAGE_TYPES_BY_ID,
    FILTER_TYPES_BY_ID,
    FilterEntityType,
    FilterMessageType,
    FilterType,
)
from models import Filter, Source
from plugins.bot.menu.utils import buttons, custom_filters
from plugins.bot.menu.utils.checks import is_admin
from plugins.bot.menu.utils.links import get_channel_formatted_link
from plugins.bot.menu.utils.managers import input_wait_manager
from plugins.bot.menu.utils.path import Path
from plugins.bot.menu.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/s_\d+/$'),
)
async def list_types_filters(_, callback_query: CallbackQuery, *, needs_an_answer=True):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get_or_none(id=source_id)

    text = '**Общие фильтры**'
    inline_keyboard = []
    if source_obj:
        text = (
            '\nКатегория: '
            f'**{await get_channel_formatted_link(source_obj.category.tg_id)}**\n'
            'Источник: '
            f'**{await get_channel_formatted_link(source_obj.tg_id)}**'
        )
        if is_admin(callback_query.from_user.id):
            inline_keyboard.append(
                [
                    InlineKeyboardButton(f'📝', callback_data=path.add_action('edit')),
                    InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
                ]
            )

    source_where = None if source_id else Filter.source.is_null(True)
    query = (
        Filter.select(Filter.type, peewee.fn.Count(Filter.id).alias('count'))
        .where(source_where if source_where else Filter.source == source_id)
        .group_by(Filter.type)
    )
    data = {filter_type.value: (filter_type.name, 0) for filter_type in FilterType}
    data.update(
        {item.type: (FILTER_TYPES_BY_ID.get(item.type), item.count) for item in query}
    )
    inline_keyboard += buttons.get_list(
        data=data,
        path=path,
        prefix_path='t',
    )
    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard + buttons.get_footer(path)),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/t_\w+/$'),
)
async def list_filters(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_type = int(path.get_value('t'))
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id) if source_id else None

    if source_obj:
        text = (
            'Категория: '
            f'**{await get_channel_formatted_link(source_obj.category.tg_id)}**\n'
            'Источник: '
            f'**{await get_channel_formatted_link(source_obj.tg_id)}**'
        )
    else:
        text = '**Общие фильтры**'
    text += f'\nФильтр: **{FILTER_TYPES_BY_ID.get(filter_type)}**'

    inline_keyboard = []
    if is_admin(callback_query.from_user.id):
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    '➕ Добавить фильтр',
                    callback_data=path.add_action('add'),
                )
            ]
        )

    source_where = None if source_id else Filter.source.is_null(True)
    query = Filter.select().where(
        (source_where if source_where else Filter.source == source_id)
        & (Filter.type == filter_type)
    )
    inline_keyboard += buttons.get_list(
        data={f'{item.id}': (item.pattern, 0) for item in query},
        path=path,
        prefix_path='f',
    )

    if needs_an_answer:
        await callback_query.answer()

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard + buttons.get_footer(path)),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/f_\d+/$'),
)
async def detail_filter(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_obj: Filter = Filter.get(id=int(path.get_value('f')))

    inline_keyboard = []
    if is_admin(callback_query.from_user.id):
        if filter_obj.type in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            inline_keyboard.append(
                [
                    InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
                ],
            )
        else:
            inline_keyboard.append(
                [
                    InlineKeyboardButton(f'📝', callback_data=path.add_action('edit')),
                    InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
                ],
            )
    inline_keyboard += buttons.get_footer(path)

    if filter_obj.source:
        text = (
            f'Источник: **{await get_channel_formatted_link(filter_obj.source.tg_id)}**'
        )
    else:
        text = '**Общий фильтр**'
    text += (
        f'\nТип фильтра: **{FILTER_TYPES_BY_ID.get(filter_obj.type)}**'
        f'\nПаттерн: `{filter_obj.pattern}`'
    )
    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/s_\d+/t_\w+/:add/$') & custom_filters.admin_only,
)
async def add_filter(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get_or_none(id=source_id)
    filter_type = int(path.get_value('t'))

    if filter_type in (
        FilterType.HASHTAG.value,
        FilterType.URL.value,
        FilterType.TEXT.value,
        FilterType.ONLY_WHITE_TEXT.value,
    ):
        text = 'ОК. Ты добавляешь '
        text += (
            'фильтр для источника '
            f'{await get_channel_formatted_link(source_obj.tg_id)} '
            if source_obj
            else 'общий фильтр '
        )
        text += (
            f'типа **{FILTER_TYPES_BY_ID.get(filter_type)}**. '
            'Паттерн является регулярным выражением '
            'с игнорированием регистра.\n\n'
            '**Введи паттерн нового фильтра:**'
        )

        await callback_query.answer()
        await callback_query.message.reply(text, disable_web_page_preview=True)
        input_wait_manager.add(
            chat_id,
            add_filter_waiting_input,
            client,
            callback_query,
            filter_type,
            source_obj,
        )
        return

    if source_obj:
        text = (
            'Категория: '
            f'**{await get_channel_formatted_link(source_obj.category.tg_id)}**\n'
            'Источник: '
            f'**{await get_channel_formatted_link(source_obj.tg_id)}**'
        )
    else:
        text = '**Общие фильтры**'
    text += (
        f'\nТип: **{FILTER_TYPES_BY_ID.get(filter_type)}**\n\n'
        'Выбери паттерн для фильтра:'
    )

    query = Filter.select().where(
        (Filter.type == filter_type) & (Filter.source == source_obj)
    )
    existing_filters_patterns = {filter_obj.pattern for filter_obj in query}
    data = {}
    if filter_type == FilterType.ENTITY_TYPE.value:
        for entity_type in FilterEntityType:
            if entity_type.name not in existing_filters_patterns:
                data.update({entity_type.value: (entity_type.name, 0)})
    else:
        for entity_type in FilterMessageType:
            if entity_type.name not in existing_filters_patterns:
                data.update({entity_type.value[0]: (entity_type.name, 0)})

    inline_keyboard = buttons.get_list(
        data=data,
        path=path,
        prefix_path='v',
    )

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard + buttons.get_footer(path)),
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/s_\d+/t_\w+/:add/v_\w+/$') & custom_filters.admin_only,
)
async def add_filter_choice_value(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get_or_none(id=source_id)
    filter_type = int(path.get_value('t'))
    value = int(path.get_value('v', after_action=True))

    if filter_type == FilterType.ENTITY_TYPE.value:
        pattern = FILTER_ENTITY_TYPES_BY_ID.get(value)
    else:
        pattern = FILTER_MESSAGE_TYPES_BY_ID.get(value)

    filter_obj = Filter.create(pattern=pattern, type=filter_type, source=source_obj)
    Filter.clear_actual_cache()

    if source_obj:
        success_text = (
            '✅ Фильтр для источника '
            f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        )
    else:
        success_text = '✅ Общий фильтр '
    success_text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** '
        f'со значением `{filter_obj.pattern}` добавлен'
    )

    await callback_query.answer(success_text)
    callback_query.data = path.get_prev(2)
    await list_filters(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)


async def add_filter_waiting_input(
    client: Client,
    message: Message,
    callback_query,
    filter_type,
    source_obj,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_footer(path, back_title='Параметры')
            ),
            disable_web_page_preview=True,
        )

    filter_obj = Filter.create(
        pattern=message.text, type=filter_type, source=source_obj
    )
    Filter.clear_actual_cache()

    if source_obj:
        success_text = (
            '✅ Фильтр для источника '
            f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        )
    else:
        success_text = '✅ Общий фильтр '
    success_text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** '
        f'с паттерном `{filter_obj.pattern}` добавлен'
    )

    await reply(success_text)

    callback_query.data = path.get_prev()
    await list_filters(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)


@Client.on_callback_query(
    filters.regex(r'/f_\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_body_filter(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get_or_none(id=filter_id)

    text = 'ОК. Ты изменяешь '
    text += (
        'фильтр для источника '
        f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        if filter_obj.source
        else 'общий фильтр '
    )
    text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** с паттерном '
        f'`{filter_obj.pattern}`.\n\n'
        '**Введи новый паттерн фильтра:**'
    )

    await callback_query.answer()
    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        chat_id, edit_body_filter_wait_input, client, callback_query, filter_obj
    )


async def edit_body_filter_wait_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
    filter_obj: Filter,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_footer(
                    path,
                    back_title='Параметры',
                )
            ),
            disable_web_page_preview=True,
        )

    filter_obj.pattern = message.text
    filter_obj.save()
    Filter.clear_actual_cache()

    if filter_obj.source:
        success_text = (
            '✅ Фильтр для источника '
            f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        )
    else:
        success_text = '✅ Общий фильтр '
    success_text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** '
        f'с паттерном `{filter_obj.pattern}` изменен'
    )

    await reply(success_text)

    callback_query.data = path.get_prev()
    await detail_filter(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)


@Client.on_callback_query(
    filters.regex(r'f_\d+/:delete/') & custom_filters.admin_only,
)
async def delete_filter(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get(id=filter_id)
    if filter_obj.source:
        text = (
            f'Источник: **{await get_channel_formatted_link(filter_obj.source.tg_id)}**'
        )
    else:
        text = '**Общий фильтр**'
    text += (
        f'\nТип фильтра: **{FILTER_TYPES_BY_ID.get(filter_obj.type)}**'
        f'\nПаттерн: `{filter_obj.pattern}`'
    )

    if path.with_confirmation:
        q = Filter.delete().where(Filter.id == filter_id)
        q.execute()

        Filter.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Фильтр удален')
        await list_filters(client, callback_query)

        await send_message_to_admins(
            client, callback_query, f'❌ Удален фильтр:\n{text}'
        )
        return

    text += '\n\nТы **удаляешь** фильтр!'

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        '❌ Подтвердить удаление', callback_data=f'{path}/'
                    ),
                ]
            ]
            + buttons.get_footer(path)
        ),
        disable_web_page_preview=True,
    )
