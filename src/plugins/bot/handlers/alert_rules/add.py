from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_user_formatted_link


@Client.on_callback_query(
    filters.regex(r"/r/:add/$") & custom_filters.admin_only,
)
async def add_alert_rule(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    menu.add_row_button("regex", "regex")
    menu.add_row_button("counter", "counter")

    category_id = menu.path.get_value("c")
    text = await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"**Новое {'' if category_id else 'общее '}правило уведомления "
            f"{await get_user_formatted_link(callback_query.from_user.id)}**\n\n"
            "Выбери тип правила"
        ),
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
