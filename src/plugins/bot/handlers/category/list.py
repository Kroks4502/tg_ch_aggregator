import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Source
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.statistic import get_statistic_text
from utils.menu import ButtonData


@Client.on_callback_query(
    filters.regex(r"/c/(p/\d+/|)$"),
)
async def list_category(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    if is_admin(callback_query.from_user.id):
        menu.add_button.add()

    query = (
        Category.select(
            Category.id,
            Category.title,
            peewee.fn.Count(Source.id).alias("amount"),
        )
        .join(Source, peewee.JOIN.LEFT_OUTER)
        .group_by(Category.id)
        .order_by(Category.title)
    )  # Запрашиваем список категорий

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.title, i.id, i.amount)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    await callback_query.message.edit_text(
        text=f"**Категории**\n\n{get_statistic_text()}",
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
