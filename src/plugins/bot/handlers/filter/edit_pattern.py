from pyrogram.types import Message

from models import Filter
from plugins.bot import router, validators
from plugins.bot.handlers.filter.common.constants import (
    SUCCESS_FILTER_PATTERN_EDIT_TEXT,
)
from plugins.bot.handlers.filter.common.utils import (
    get_dialog_enter_pattern_text,
    get_filter_menu_success_text,
)
from plugins.bot.menu import Menu


@router.wait_input(send_to_admins=True)
async def edit_body_filter_wait_input(
    message: Message,
    menu: Menu,
):
    pattern_new = str(message.text)
    validators.is_valid_pattern(pattern_new)

    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(id=filter_id)

    pattern_old = filter_obj.pattern
    filter_obj.pattern = pattern_new
    filter_obj.save()

    return await get_filter_menu_success_text(
        filter_obj=filter_obj,
        action=SUCCESS_FILTER_PATTERN_EDIT_TEXT.format(pattern_new, pattern_old),
    )


@router.page(
    path=r"/f/\d+/:edit/",
    reply=True,
    add_wait_for_input=edit_body_filter_wait_input,
)
async def edit_body_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(id=filter_id)

    return await get_dialog_enter_pattern_text(
        filter_type_id=menu.path.get_value("ft"),
        source_id=menu.path.get_value("s"),
        action="изменяешь",
        pattern=filter_obj.pattern,
    )
