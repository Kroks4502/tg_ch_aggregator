from models import Filter
from plugins.bot import router
from plugins.bot.handlers.filter.common.constants import (
    PLURAL_COMMON_FILTER_TITLE,
    PLURAL_FILTER_TITLE,
)
from plugins.bot.handlers.filter.common.utils import get_filter_menu_text
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/ft/\d+/f/", pagination=True, back_step=2)
async def list_filters(menu: Menu):
    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")

    if menu.is_admin_user():
        menu.add_button.add()

    if source_id:
        query = Filter.select().where(
            (Filter.source == source_id) & (Filter.type == filter_type_id)
        )
    else:
        query = Filter.select().where(
            Filter.source.is_null(True) & (Filter.type == filter_type_id)
        )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.pattern, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return await get_filter_menu_text(
        title=PLURAL_FILTER_TITLE,
        title_common=PLURAL_COMMON_FILTER_TITLE,
        source_id=source_id,
        filter_type_id=filter_type_id,
    )
