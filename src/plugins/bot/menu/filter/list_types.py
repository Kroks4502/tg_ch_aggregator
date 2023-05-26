import logging

import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from filter_types import FilterType, FILTER_TYPES_BY_ID
from models import Source, Filter
from plugins.bot.utils import buttons
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path


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
