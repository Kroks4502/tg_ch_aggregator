import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from clients import user
from models import Admin
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_user_formatted_link
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'^/o/a/u_\d+/$') & custom_filters.admin_only,
)
async def detail_admin(_, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    admin_id = int(path.get_value('u'))
    admin_obj: Admin = Admin.get(id=admin_id)
    text = f'**{await get_user_formatted_link(admin_obj.tg_id)}**\n\n'

    inline_keyboard = []
    if admin_obj.tg_id != user.me.id:
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    '✖️ Удалить',
                    callback_data=path.add_action('delete'),
                ),
            ]
        )
    inline_keyboard += buttons.get_footer(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )
