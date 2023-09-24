import peewee

from models import Category, Filter, Source
from plugins.bot import router
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/s/", pagination=True)
async def list_source(menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj = Category.get(category_id) if category_id else None

    if category_obj and menu.is_admin_user():
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

    return await menu.get_text(
        category_obj=category_obj,
        last_text="**Источники**",
    )
