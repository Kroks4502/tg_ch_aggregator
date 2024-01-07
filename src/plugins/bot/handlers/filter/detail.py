from peewee import DoesNotExist

from filter_types import FilterType
from models import Filter, MessageHistory
from plugins.bot import router
from plugins.bot.constants.settings import FORMAT_TIMESTAMP
from plugins.bot.handlers.filter.common.constants import (
    FILTER_LAST_FIRED_CONTENT,
    FILTER_NOT_FOUND,
    SINGULAR_COMMON_FILTER_TITLE,
    SINGULAR_FILTER_TITLE,
)
from plugins.bot.handlers.filter.common.utils import get_filter_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/f/\d+/", command=True)
async def filter_detail(menu: Menu):
    filter_id = menu.path.get_value("f")
    try:
        filter_obj: Filter = Filter.get(filter_id)
    except DoesNotExist:
        return FILTER_NOT_FOUND

    if menu.is_admin_user():
        if filter_obj.type not in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            menu.add_button.edit()
        menu.add_button.delete()

    try:
        history_obj = (
            MessageHistory.select()
            .where(MessageHistory.filter_id == filter_obj.id)
            .order_by(MessageHistory.id.desc())
            .get()
        )
        content = FILTER_LAST_FIRED_CONTENT.format(
            history_obj.created_at.strftime(FORMAT_TIMESTAMP)
        )
    except DoesNotExist:
        content = None

    return await get_filter_menu_text(
        title=SINGULAR_FILTER_TITLE,
        title_common=SINGULAR_COMMON_FILTER_TITLE,
        source_id=filter_obj.source_id,
        filter_type_id=filter_obj.type,
        pattern=filter_obj.pattern,
        content=content,
    )
