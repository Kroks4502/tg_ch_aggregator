from models import GlobalSettings, Source
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/cl/", pagination=True)
async def list_cleanup(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj and menu.is_admin_user():
        cleanup_list = source_obj.cleanup_list
    else:
        cleanup_list = GlobalSettings.get(key="cleanup_list").value
    menu.add_button.add()

    pagination = menu.set_pagination(total_items=len(cleanup_list))

    for idx, reg in enumerate(
        cleanup_list[pagination.offset : pagination.offset_with_size],
        pagination.offset,
    ):
        menu.add_row_button(reg, str(idx))

    return await menu.get_text(
        source_obj=source_obj,
        last_text="**Очистка текста**" if source_obj else "**Общая очистка текста**",
    )
