from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from filter_types import (
    FILTER_ENTITY_TYPES_BY_ID,
    FILTER_MESSAGE_TYPES_BY_ID,
    FILTER_TYPES_BY_ID,
    FilterType,
)
from models import Filter, Source
from plugins.bot.constants import INVALID_PATTERN_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import ButtonData, Menu
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins

ASK_TEXT_TPL = (
    'ОК. Ты добавляешь {} типа **{}**. Паттерн является регулярным выражением '
    'с игнорированием регистра.\n\n**Введи паттерн:**'
)
SUC_TEXT_TPL = '✅ {} типа **{}** c паттерном `{}` добавлен'


@Client.on_callback_query(
    filters.regex(r'/ft/\d+/f/:add/$') & custom_filters.admin_only,
)
async def add_filter(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)
    filter_type_id = path.get_value('ft')
    if filter_type_id in (
        FilterType.HASHTAG.value,
        FilterType.URL.value,
        FilterType.TEXT.value,
        FilterType.ONLY_WHITE_TEXT.value,
    ):
        await ask_filter_pattern(client, callback_query)
        return

    await add_filter_with_choice(callback_query)


async def ask_filter_pattern(client: Client, callback_query: CallbackQuery):
    path = Path(callback_query.data)

    filter_type_id = path.get_value('ft')
    source_id = path.get_value('s')  # Может быть 0
    source_obj: Source = Source.get(id=source_id) if source_id else None

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.tg_id)
        title = f'фильтр для источника {src_link}'
    else:
        title = 'общий фильтр'
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)
    text = ASK_TEXT_TPL.format(title, filter_type_text)

    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        callback_query.message.chat.id,
        ask_filter_pattern_waiting_input,
        client,
        callback_query,
        filter_type_id,
        source_obj,
    )


async def ask_filter_pattern_waiting_input(
    client: Client,
    message: Message,
    callback_query,
    filter_type,
    source_obj,
):
    menu = Menu(callback_query.data)

    async def reply(t):
        await message.reply_text(
            text=t,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    pattern = message.text
    if not is_valid_pattern(pattern):
        await reply(INVALID_PATTERN_TEXT)
        return

    filter_obj = Filter.create(
        pattern=pattern,
        type=filter_type,
        source=source_obj,
    )
    Filter.clear_actual_cache()

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.tg_id)
        title = f'Фильтр для источника {src_link}'
    else:
        title = 'Общий фильтр'
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    text = SUC_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)

    await reply(text)

    await send_message_to_admins(client, callback_query, text)


async def add_filter_with_choice(callback_query: CallbackQuery):
    menu = Menu(callback_query.data)

    filter_type_id = menu.path.get_value('ft')

    source_id = menu.path.get_value('s')  # Может быть 0
    source_obj: Source = Source.get(id=source_id) if source_id else None

    query = Filter.select().where(
        (Filter.type == filter_type_id) & (Filter.source == source_obj)
    )

    used_patterns = {i.pattern for i in query}

    data = []
    if filter_type_id == FilterType.ENTITY_TYPE.value:
        filter_enum = FILTER_ENTITY_TYPES_BY_ID
    else:
        filter_enum = FILTER_MESSAGE_TYPES_BY_ID

    for value, name in filter_enum.items():
        if name not in used_patterns:
            data.append(ButtonData(name, value))

    menu.add_rows_from_data(data)

    text = await menu.get_text(source_obj=source_obj, filter_type_id=filter_type_id)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/ft/\d+/f/:add/\d+/$') & custom_filters.admin_only,
)
async def select_filter_value(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(id=source_id) if source_id else None

    filter_type_id = menu.path.get_value('ft')
    filter_value = menu.path.get_value(':add')

    if filter_type_id == FilterType.ENTITY_TYPE.value:
        pattern = FILTER_ENTITY_TYPES_BY_ID.get(filter_value)
    else:
        pattern = FILTER_MESSAGE_TYPES_BY_ID.get(filter_value)

    Filter.create(
        pattern=pattern,
        type=filter_type_id,
        source=source_obj,
    )
    Filter.clear_actual_cache()

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.tg_id)
        title = f'Фильтр для источника {src_link}'
    else:
        title = 'Общий фильтр'
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)
    text = SUC_TEXT_TPL.format(title, filter_type_text, pattern)

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
