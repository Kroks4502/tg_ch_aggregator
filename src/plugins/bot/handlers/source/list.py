import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Filter, Source
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin
from utils.menu import ButtonData


@Client.on_callback_query(
    filters.regex(r"/s/(p/\d+/|)$"),
)
async def list_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data)

    category_id = menu.path.get_value("c")
    category_obj = Category.get(category_id) if category_id else None
    if category_obj and is_admin(callback_query.from_user.id):
        menu.add_button.add()

    query = (
        Source.select(
            Source.id,
            Source.title,
            Source.title_alias,
            Source.cleanup_list,
            peewee.fn.Count(Filter.id).alias("count"),
        )
        .where(Source.category == category_obj.id if category_obj else True)
        .join(Filter, peewee.JOIN.LEFT_OUTER)
        .group_by(Source.id)
        .order_by(Source.title)
    )  # Запрашиваем список источников

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.title_alias or i.title, i.id, i.count + len(i.cleanup_list))
            for i in query.paginate(pagination.page, pagination.size)
        ]
    )

    await callback_query.message.edit_text(
        text=await menu.get_text(
            category_obj=category_obj,
            last_text="**Источники**",
        ),
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
