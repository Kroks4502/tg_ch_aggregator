from pyrogram.types import Message

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

ASK_TEXT_TPL = (
    "ОК. Ты изменяешь {} типа **{}** с паттерном `{}`\n\n"
    f"**Введи новый паттерн** или {CANCEL}"
)
SUC_TEXT_TPL = "✅ {} типа **{}** с паттерном `{}` изменен на `{}`"


@router.wait_input(send_to_admins=True)
async def edit_body_filter_wait_input(
    message: Message,
    menu: Menu,
):
    pattern_new = str(message.text)
    validators.is_valid_pattern(pattern_new)

    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(id=filter_id) if filter_id else None

    pattern_old = filter_obj.pattern

    filter_obj.pattern = pattern_new
    filter_obj.save()

    if filter_obj.source:
        src_link = await get_channel_formatted_link(filter_obj.source.id)
        title = f"Фильтр для источника {src_link}"
    else:
        title = "Общий фильтр"

    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)

    return SUC_TEXT_TPL.format(title, filter_type_text, pattern_old, pattern_new)


@router.page(path=r"/f/\d+/:edit/", add_wait_for_input=edit_body_filter_wait_input)
async def edit_body_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(id=filter_id) if filter_id else None

    if filter_obj.source:
        src_link = {await get_channel_formatted_link(filter_obj.source.id)}
        title = f"фильтр для источника {src_link}"
    else:
        title = "общий фильтр"
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)

    return ASK_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)
