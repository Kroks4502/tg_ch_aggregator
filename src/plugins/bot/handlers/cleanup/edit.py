from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.bot import router, validators
from plugins.bot.handlers.cleanup.common.utils import (
    get_cleanup_menu_success_text,
    get_dialog_enter_pattern_text,
)
from plugins.bot.menu import Menu


@router.wait_input(send_to_admins=True)
async def edit_cleanup_regex_wait_input(
    message: Message,
    menu: Menu,
):
    validators.is_text(message)

    pattern_new = str(message.text)
    validators.is_valid_pattern(pattern_new)

    cleanup_id = menu.path.get_value("cl")
    source_id = menu.path.get_value("s")
    if source_id:
        source_obj: Source = (
            Source.get(id=source_id, is_deleted=False) if source_id else None
        )
        cleanup_list = source_obj.cleanup_list
        pattern_old = cleanup_list[cleanup_id]
        cleanup_list[cleanup_id] = pattern_new
        source_obj.save()
    else:
        global_settings_obj = GlobalSettings.get(key="cleanup_list")
        cleanup_list = global_settings_obj.value
        pattern_old = cleanup_list[cleanup_id]
        cleanup_list[cleanup_id] = pattern_new
        global_settings_obj.save()

    return await get_cleanup_menu_success_text(
        source_id=source_id,
        pattern=pattern_old,
        action=f"изменен на `{pattern_new}`",
    )


@router.page(
    path=r"/cl/\d+/:edit/",
    reply=True,
    add_wait_for_input=edit_cleanup_regex_wait_input,
)
async def edit_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")
    source_id = menu.path.get_value("s")

    if source_id:
        source_obj: Source = Source.get(id=source_id, is_deleted=False)
        pattern = source_obj.cleanup_list[cleanup_id]
    else:
        global_settings_obj = GlobalSettings.get(key="cleanup_list")
        pattern = global_settings_obj.value[cleanup_id]

    return await get_dialog_enter_pattern_text(
        source_id=source_id,
        action="изменяешь",
        pattern=pattern,
    )
