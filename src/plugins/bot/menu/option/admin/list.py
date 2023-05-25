import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from models import Admin
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'^/o/a/$') & custom_filters.admin_only,
)
async def list_admins(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    text = f'**Список администраторов:**'

    inline_keyboard = [
        [
            InlineKeyboardButton('✖ Добавить', callback_data=path.add_action('add')),
        ]
    ]

    query = Admin.select(
        Admin.id,
        Admin.username,
    )
    inline_keyboard += buttons.get_list(
        data={f'{item.id}': (item.username, 0) for item in query},
        path=path,
        prefix_path='u',
    )
    inline_keyboard += buttons.get_footer(path)
    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )
