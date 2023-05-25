import logging
import math

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from common import get_shortened_text, get_message_link
from filter_types import FILTER_TYPES_BY_ID
from models import FilterMessageHistory
from plugins.bot.constants import MAX_NUM_ENTRIES_MESSAGE
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'^/o/fh/$|^/o/fh/p_\d+/$') & custom_filters.admin_only,
)
async def filter_history(_, callback_query: CallbackQuery):
    logging.debug(callback_query.data)
    page = int(p) if (p := Path(callback_query.data).get_value('p')) else 1
    query = FilterMessageHistory.select().order_by(FilterMessageHistory.id.desc())
    obj_counts = query.count()
    text = '**Список отфильтрованных сообщений в обратном порядке**\n\n'
    for item in query.paginate(page, MAX_NUM_ENTRIES_MESSAGE):
        text += (
            f'{"🏞" if item.media_group else "🗞"}'
            f'[{get_shortened_text(item.source.title, 30)}]'
            f'({get_message_link(item.source.tg_id, item.source_message_id)})\n'
            f'**{"Персональный" if item.filter.source else "Общий"}** фильтр '
            f'**{FILTER_TYPES_BY_ID.get(item.filter.type)}**\n'
            f'`{item.filter.pattern}`\n'
            f'__{item.source_message_id} {item.date.strftime("%Y.%m.%d, %H:%M:%S")}__'
            '\n\n'
        )
    text += f'Всего записей: **{obj_counts}**'
    inline_keyboard = [[]]
    if page > 1:
        inline_keyboard[0].append(
            InlineKeyboardButton('Предыдущие', callback_data=f'/o/fh/p_{page - 1}/')
        )
    if page < math.ceil(obj_counts / MAX_NUM_ENTRIES_MESSAGE):
        inline_keyboard[0].append(
            InlineKeyboardButton('Следующие', callback_data=f'/o/fh/p_{page + 1}/')
        )
    inline_keyboard += buttons.get_footer(Path('/o/fh/'))
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
