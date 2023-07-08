from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.constants import INVALID_PATTERN_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins

ASK_TEXT_TPL = (
    'ОК. Ты изменяешь {} типа **{}** с паттерном `{}`\n\n**Введи новый паттерн:**'
)
SUC_TEXT_TPL = '✅ {} типа **{}** с паттерном `{}` изменен на `{}`'


@Client.on_callback_query(
    filters.regex(r'/f/\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_body_filter(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)

    filter_id = path.get_value('f')
    filter_obj: Filter = Filter.get(id=filter_id) if filter_id else None

    if filter_obj.source:
        src_link = {await get_channel_formatted_link(filter_obj.source.id)}
        title = f'фильтр для источника {src_link}'
    else:
        title = 'общий фильтр'
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    text = ASK_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)

    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_body_filter_wait_input,
        client,
        callback_query,
        filter_obj,
    )


async def edit_body_filter_wait_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
    filter_obj: Filter,
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

    pattern_new = message.text
    if not is_valid_pattern(pattern_new):
        await reply(INVALID_PATTERN_TEXT)
        return

    pattern_old = filter_obj.pattern

    filter_obj.pattern = pattern_new
    filter_obj.save()
    Filter.clear_actual_cache()

    if filter_obj.source:
        src_link = await get_channel_formatted_link(filter_obj.source.id)
        title = f'Фильтр для источника {src_link}'
    else:
        title = 'Общий фильтр'

    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    text = SUC_TEXT_TPL.format(title, filter_type_text, pattern_old, pattern_new)

    await reply(text)

    await send_message_to_admins(client, callback_query, text)
