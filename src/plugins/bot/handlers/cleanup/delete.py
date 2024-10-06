from models import GlobalSettings, Source
from plugins.bot import router
from plugins.bot.handlers.cleanup.common.constants import QUESTION_CONF_DEL
from plugins.bot.handlers.cleanup.common.utils import (
    get_cleanup_menu_success_text,
    get_cleanup_menu_text,
)
from plugins.bot.menu import Menu


@router.page(path=r"/cl/\d+/:delete/")
async def cleanup_regex_deletion_confirmation(menu: Menu):
    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    if source_id:
        source_obj: Source = Source.get(
            id=source_id,
            is_deleted=False,
        )
        pattern = source_obj.cleanup_list[cleanup_id]
    else:
        cleanup_list = GlobalSettings.get(key="cleanup_list").value
        pattern = cleanup_list[cleanup_id]

    menu.add_button.confirmation_delete()

    return await get_cleanup_menu_text(
        source_id=source_id,
        pattern=pattern,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/cl/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")
    source_id = menu.path.get_value("s")

    if source_id:
        source_obj: Source = Source.get(id=source_id, is_deleted=False)
        pattern = source_obj.cleanup_list.pop(cleanup_id)
        source_obj.save()
    else:
        global_settings_obj = GlobalSettings.get(key="cleanup_list")
        pattern = global_settings_obj.value.pop(cleanup_id)
        global_settings_obj.save()

    return await get_cleanup_menu_success_text(
        source_id=source_id,
        pattern=pattern,
        action="удален",
    )
