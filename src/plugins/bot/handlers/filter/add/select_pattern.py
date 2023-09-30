from filter_types import (
    FILTER_ENTITY_TYPES_BY_ID,
    FILTER_MESSAGE_TYPES_BY_ID,
    FilterType,
)
from models import Filter
from plugins.bot import router
from plugins.bot.handlers.filter.common.constants import (
    NEW_COMMON_FILTER_TITLE,
    NEW_FILTER_TITLE,
    QUESTION_SELECT_PATTERN,
    SUCCESS_FILTER_PATTERN_ADD_TEXT,
)
from plugins.bot.handlers.filter.common.utils import (
    get_filter_menu_success_text,
    get_filter_menu_text,
)
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/ft/(4|5)/f/:add/")
async def add_filter_with_selected_pattern(menu: Menu):
    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")

    query_used_patterns = Filter.select(Filter.pattern).group_by(Filter.pattern)
    where = Filter.type == filter_type_id
    if source_id:
        query_used_patterns = query_used_patterns.where(
            where & ((Filter.source_id == source_id) | (Filter.source_id.is_null()))
        )
    else:
        query_used_patterns = query_used_patterns.where(
            where & (Filter.source_id.is_null())
        )

    if filter_type_id == FilterType.ENTITY_TYPE.value:
        filter_enum = FILTER_ENTITY_TYPES_BY_ID
    else:
        filter_enum = FILTER_MESSAGE_TYPES_BY_ID

    menu.add_rows_from_data(
        [
            ButtonData(name, value)
            for value, name in filter_enum.items()
            if name not in {i.pattern for i in query_used_patterns}
        ]
    )

    return await get_filter_menu_text(
        title=NEW_FILTER_TITLE,
        title_common=NEW_COMMON_FILTER_TITLE,
        source_id=source_id,
        filter_type_id=filter_type_id,
        question=QUESTION_SELECT_PATTERN,
    )


@router.page(path=r"/ft/(4|5)/f/:add/\d+/", back_step=2, send_to_admins=True)
async def filter_pattern_selection(menu: Menu):
    source_id = menu.path.get_value("s")
    filter_type_id = menu.path.get_value("ft")
    filter_value = menu.path.get_value(":add")

    if filter_type_id == FilterType.ENTITY_TYPE.value:
        pattern = FILTER_ENTITY_TYPES_BY_ID.get(filter_value)
    else:
        pattern = FILTER_MESSAGE_TYPES_BY_ID.get(filter_value)

    filter_obj = Filter.create(
        pattern=pattern,
        type=filter_type_id,
        source_id=source_id,
    )

    return await get_filter_menu_success_text(
        filter_obj=filter_obj,
        action=SUCCESS_FILTER_PATTERN_ADD_TEXT.format(filter_obj.pattern),
    )
