import logging

import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from models import Category, Source, Filter
from plugins.bot.utils import buttons
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'^/c_\d+/$'),
)
async def list_source(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    category_id = int(path.get_value('c'))
    category_obj: Category = Category.get(id=category_id) if category_id else None

    text = (
        f'Категория: **{await get_channel_formatted_link(category_obj.tg_id)}**'
        if category_obj
        else '**Все источники**'
    )

    inline_keyboard = []
    if category_obj and is_admin(callback_query.from_user.id):
        inline_keyboard.append(
            [
                InlineKeyboardButton('➕', callback_data=path.add_action('add')),
                InlineKeyboardButton(f'📝', callback_data=path.add_action('edit')),
                InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
            ]
        )
    query = (
        Source.select(
            Source.id, Source.title, peewee.fn.Count(Filter.id).alias('count')
        )
        .where(Source.category == category_id if category_id else True)
        .join(Filter, peewee.JOIN.LEFT_OUTER)
        .group_by(Source.id)
    )
    inline_keyboard += buttons.get_list(
        data={item.id: (item.title, item.count) for item in query},
        path=path,
        prefix_path='s',
    ) + buttons.get_footer(path)

    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )
