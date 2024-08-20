from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.bot import router, validators
from plugins.bot.handlers.cleanup.common.utils import (
    get_cleanup_menu_success_text,
    get_dialog_enter_pattern_text,
)
from plugins.bot.menu import Menu


@router.wait_input(send_to_admins=True)
async def add_cleanup_regex_waiting_input(
    message: Message,
    menu: Menu,
):
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    source_id = menu.path.get_value("s")
    if source_id:
        source_obj: Source = Source.get(
            id=source_id,
            is_deleted=False,
        )
        source_obj.cleanup_list.append(pattern)
        source_obj.save()
    else:
        global_settings_obj = GlobalSettings.get(key="cleanup_list")
        global_settings_obj.value.append(pattern)
        global_settings_obj.save()

    return await get_cleanup_menu_success_text(
        source_id=source_id,
        pattern=pattern,
        action="добавлен",
    )


@router.page(
    path=r"/cl/:add/",
    reply=True,
    add_wait_for_input=add_cleanup_regex_waiting_input,
)
async def add_cleanup_regex(menu: Menu):
    source_id = menu.path.get_value("s")
    return await get_dialog_enter_pattern_text(
        source_id=source_id,
        action="добавляешь",
    )
