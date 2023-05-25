import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from filter_types import (
    FilterType,
    FILTER_TYPES_BY_ID,
    FilterEntityType,
    FilterMessageType,
    FILTER_ENTITY_TYPES_BY_ID,
    FILTER_MESSAGE_TYPES_BY_ID,
)
from models import Source, Filter
from plugins.bot.menu.filter.list import list_filters
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


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
