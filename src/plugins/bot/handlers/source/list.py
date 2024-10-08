import peewee

from models import Filter, Source
from plugins.bot import router
from plugins.bot.handlers.source.common.constants import PLURAL_SOURCE_TITLE
from plugins.bot.handlers.source.common.utils import get_source_menu_text
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/s/", pagination=True)
async def list_source(menu: Menu):
    query = (
        Source.select(
            Source.id,
            Source.title,
            Source.title_alias,
            Source.cleanup_list,
            peewee.fn.Count(Filter.id).alias("count"),
        )
        .join(Filter, peewee.JOIN.LEFT_OUTER)
        .where(Source.is_deleted == False)
        .group_by(Source.id)
        .order_by(Source.title)
    )  # Запрашиваем список источников

    category_id = menu.path.get_value("c")
    if category_id:
        query = query.where(Source.category == category_id)
        if menu.is_admin_user():
            menu.add_button.add()

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.title_alias or i.title, i.id, i.count + len(i.cleanup_list))
            for i in query.paginate(pagination.page, pagination.size)
        ]
    )

    return await get_source_menu_text(
        title=PLURAL_SOURCE_TITLE,
        category_id=category_id,
    )
