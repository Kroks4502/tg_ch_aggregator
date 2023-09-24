from filter_types import (
    FILTER_ENTITY_TYPES_BY_ID,
    FILTER_MESSAGE_TYPES_BY_ID,
    FILTER_TYPES_BY_ID,
    FilterType,
)
from models import Filter, Source
from plugins.bot import router
from plugins.bot.handlers.filter.add import SUC_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link
from utils.menu import ButtonData


@router.page(path=r"/ft/(4|5)/f/:add/")
async def add_filter_with_choice(menu: Menu):
    filter_type_id = menu.path.get_value("ft")

    source_id = menu.path.get_value("s")  # Может быть 0
    source_obj: Source = Source.get(id=source_id) if source_id else None

    query = Filter.select().where(
        (Filter.type == filter_type_id) & (Filter.source == source_obj)
    )

    used_patterns = {i.pattern for i in query}

    data = []
    if filter_type_id == FilterType.ENTITY_TYPE.value:
        filter_enum = FILTER_ENTITY_TYPES_BY_ID
    else:
        filter_enum = FILTER_MESSAGE_TYPES_BY_ID

    for value, name in filter_enum.items():
        if name not in used_patterns:
            data.append(ButtonData(name, value))

    menu.add_rows_from_data(data)

    return await menu.get_text(source_obj=source_obj, filter_type_id=filter_type_id)


@router.page(path=r"/ft/(4|5)/f/:add/\d+/", back_step=2, send_to_admins=True)
async def select_filter_value(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(id=source_id) if source_id else None

    filter_type_id = menu.path.get_value("ft")
    filter_value = menu.path.get_value(":add")

    if filter_type_id == FilterType.ENTITY_TYPE.value:
        pattern = FILTER_ENTITY_TYPES_BY_ID.get(filter_value)
    else:
        pattern = FILTER_MESSAGE_TYPES_BY_ID.get(filter_value)

    Filter.create(
        pattern=pattern,
        type=filter_type_id,
        source=source_obj,
    )

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.id)
        title = f"Фильтр для источника {src_link}"
    else:
        title = "Общий фильтр"
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)

    return SUC_TEXT_TPL.format(title, filter_type_text, pattern)
