from pyrogram.types import Message

from models import Filter
from plugins.bot import router, validators
from plugins.bot.handlers.filter.common.constants import SUCCESS_FILTER_PATTERN_ADD_TEXT
from plugins.bot.handlers.filter.common.utils import (
    get_dialog_enter_pattern_text,
    get_filter_menu_success_text,
)
from plugins.bot.menu import Menu


@router.wait_input(send_to_admins=True)
async def add_filter_with_entered_pattern(
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")

    filter_obj = Filter.create(
        pattern=pattern,
        type=filter_type_id,
        source_id=source_id,
    )

    return await get_filter_menu_success_text(
        filter_obj=filter_obj,
        action=SUCCESS_FILTER_PATTERN_ADD_TEXT.format(filter_obj.pattern),
    )


@router.page(
    path=r"/ft/(1|2|3|6)/f/:add/",
    reply=True,
    add_wait_for_input=add_filter_with_entered_pattern,
)
async def request_filter_pattern(menu: Menu):
    return await get_dialog_enter_pattern_text(
        filter_type_id=menu.path.get_value("ft"),
        source_id=menu.path.get_value("s"),
        action="добавляешь",
    )
