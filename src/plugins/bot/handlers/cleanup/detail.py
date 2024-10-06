from models import GlobalSettings, Source
from plugins.bot import router
from plugins.bot.handlers.cleanup.common.utils import get_cleanup_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/cl/\d+/")
async def detail_cleanup_regex(menu: Menu):
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

    if menu.is_admin_user():
        menu.add_button.edit()
        menu.add_button.delete()

    return await get_cleanup_menu_text(
        source_id=source_id,
        pattern=pattern,
    )
