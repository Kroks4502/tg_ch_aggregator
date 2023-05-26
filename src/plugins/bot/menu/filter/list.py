import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from filter_types import FILTER_TYPES_BY_ID
from models import Source, Filter
from plugins.bot.utils import buttons
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path


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
