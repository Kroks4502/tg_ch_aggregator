from pyrogram.types import Message

from filter_types import FILTER_TYPES_BY_ID
from models import Filter, Source
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.handlers.filter.add import SUC_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(send_to_admins=True)
async def ask_filter_pattern_waiting_input(
    message: Message,
    menu: Menu,
):
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")  # Может быть 0
    source_obj: Source = Source.get(id=source_id) if source_id else None

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.id)
        title = f"Фильтр для источника {src_link}"
    else:
        title = "Общий фильтр"

    filter_obj = Filter.create(
        pattern=pattern,
        type=filter_type_id,
        source=source_obj,
    )
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)

    return SUC_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)


@router.page(
    path=r"/ft/(1|2|3|6)/f/:add/",
    reply=True,
    add_wait_for_input=ask_filter_pattern_waiting_input,
)
async def ask_filter_pattern(menu: Menu):
    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")  # Может быть 0
    source_obj: Source = Source.get(id=source_id) if source_id else None

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.id)
        title = f"фильтр для источника {src_link}"
    else:
        title = "общий фильтр"
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)

    return ASK_TEXT_TPL.format(title, filter_type_text)


ASK_TEXT_TPL = (
    "ОК. Ты добавляешь {} типа **{}**. Паттерн является регулярным выражением "
    f"с игнорированием регистра.\n\n**Введи паттерн** или {CANCEL}"
)
