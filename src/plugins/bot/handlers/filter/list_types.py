import peewee

from filter_types import FilterType
from models import Filter, Source
from plugins.bot import router
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/ft/")
async def list_types_filters(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    menu.add_button.filters_histories()

    if source_obj:
        query = (
            Filter.select(Filter.type, peewee.fn.Count(Filter.id).alias("count"))
            .where(Filter.source == source_id)
            .group_by(Filter.type)
        )
    else:
        query = (
            Filter.select(Filter.type, peewee.fn.Count(Filter.id).alias("count"))
            .where(Filter.source.is_null(True))
            .group_by(Filter.type)
        )

    amounts = {i.type: i.count for i in query}

    menu.add_rows_from_data(
        data=[
            ButtonData(ft.name, ft.value, amounts.get(ft.value, 0)) for ft in FilterType
        ],
        postfix="f/",
    )

    return await menu.get_text(
        source_obj=source_obj,
        last_text="**Фильтры**" if source_obj else "**Общие фильтры**",
    )
