from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/$"),
)
async def detail_category(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data)

    category_id = menu.path.get_value("c")
    category_obj = Category.get(category_id) if category_id else None
    if category_obj and is_admin(callback_query.from_user.id):
        menu.add_button.row_edit_delete()

    menu.add_button.sources(category_id=category_id)
    menu.add_button.alert_rules(
        user_id=callback_query.from_user.id,
        category_id=category_id,
    )
    menu.add_button.messages_histories()
    menu.add_button.filters_histories()
    menu.add_button.statistics()

    await callback_query.message.edit_text(
        text=await menu.get_text(
            category_obj=category_obj,
        ),
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
