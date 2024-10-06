import peewee

from models import Category, Source
from plugins.bot import router
from plugins.bot.handlers.category.common.utils import get_category_menu_text
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/c/", pagination=True)
async def list_category(menu: Menu):
    if menu.is_admin_user():
        menu.add_button.add()

    query = (
        Category.select(
            Category.id,
            Category.title,
            peewee.fn.Count(Source.id).alias("amount"),
        )
        .join(
            Source,
            peewee.JOIN.LEFT_OUTER,
            on=((Source.category == Category.id) & (Source.is_deleted == False)),
        )
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

    return await get_category_menu_text()
