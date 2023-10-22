import peewee

from filter_types import FilterType
from models import Filter
from plugins.bot import router
from plugins.bot.handlers.filter.common.constants import (
    PLURAL_COMMON_FILTER_TITLE,
    PLURAL_FILTER_TITLE,
)
from plugins.bot.handlers.filter.common.utils import get_filter_menu_text
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/ft/")
async def list_types_filters(menu: Menu):
    source_id = menu.path.get_value("s")

    menu.add_button.filters_histories()
    menu.add_button.filters_statistics()

    query = Filter.select(
        Filter.type, peewee.fn.Count(Filter.id).alias("count")
    ).group_by(Filter.type)
    if source_id:
        query = query.where(Filter.source == source_id)
    else:
        query = query.where(Filter.source.is_null(True))

    amounts = {i.type: i.count for i in query}
    menu.add_rows_from_data(
        data=[
            ButtonData(ft.name, ft.value, amounts.get(ft.value, 0)) for ft in FilterType
        ],
        postfix="f/",
    )

    return await get_filter_menu_text(
        title=PLURAL_FILTER_TITLE,
        title_common=PLURAL_COMMON_FILTER_TITLE,
        source_id=source_id,
    )
