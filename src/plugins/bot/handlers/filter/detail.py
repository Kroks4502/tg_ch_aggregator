from filter_types import FilterType
from models import Filter
from plugins.bot import router
from plugins.bot.handlers.filter.common.constants import (
    SINGULAR_COMMON_FILTER_TITLE,
    SINGULAR_FILTER_TITLE,
)
from plugins.bot.handlers.filter.common.utils import get_filter_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/f/\d+/")
async def filter_detail(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    if menu.is_admin_user():
        if filter_obj.type not in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            menu.add_button.edit()
        menu.add_button.delete()

    return await get_filter_menu_text(
        title=SINGULAR_FILTER_TITLE,
        title_common=SINGULAR_COMMON_FILTER_TITLE,
        source_id=filter_obj.source_id,
        filter_type_id=filter_obj.type,
        pattern=filter_obj.pattern,
    )
