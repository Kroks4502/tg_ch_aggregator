from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, MessageHistory
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.statistic import get_statistic_text


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/$"),
)
async def detail_category(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data)

    category_id = menu.path.get_value("c")
    category_obj = Category.get(category_id) if category_id else None
    if category_obj and is_admin(callback_query.from_user.id):
        menu.add_button.edit_delete()

    menu.add_button.sources(category_id=category_id)
    menu.add_button.alert_rules(
        user_id=callback_query.from_user.id,
        category_id=category_id,
    )
    menu.add_button.messages_histories()
    menu.add_button.filters_histories()

    statistic_text = get_statistic_text(where=MessageHistory.category == category_obj)
    await callback_query.message.edit_text(
        text=await menu.get_text(
            category_obj=category_obj,
            last_text=statistic_text,
        ),
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
