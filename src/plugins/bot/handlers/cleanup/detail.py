from models import GlobalSettings, Source
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/cl/\d+/")
async def detail_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj:
        pattern = source_obj.cleanup_list[cleanup_id]
    else:
        cleanup_list = GlobalSettings.get(key="cleanup_list").value
        pattern = cleanup_list[cleanup_id]

    if menu.is_admin_user():
        menu.add_button.edit()
        menu.add_button.delete()

    return await menu.get_text(source_obj=source_obj, cleanup_pattern=pattern)
