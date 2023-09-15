from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category
from plugins.bot.utils import custom_filters
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/:add/$") & custom_filters.admin_only,
)
async def add_alert_rule(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    menu.add_row_button("regex", "regex")
    menu.add_row_button("counter", "counter")

    category_id = menu.path.get_value("c")
    text = await menu.get_text(
        category_obj=Category.get(category_id),
        last_text="**Новое правило уведомлений**\n\nВыбери тип правила",
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
