import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from models import Source
from plugins.bot.menu.main import list_category_buttons
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r's_\d+/:edit/$') & custom_filters.admin_only,
)
async def choice_source_category(_, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    source_obj: Source = Source.get(id=int(path.get_value('s')))
    text = (
        f'Источник: {await get_channel_formatted_link(source_obj.tg_id)}'
        '\n\nТы **меняешь категорию** у источника.\n'
        'Выбери новую категорию:'
    )

    inline_keyboard = list_category_buttons(path) + buttons.get_footer(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )
