from models import Source
from plugins.bot import router
from plugins.bot.handlers.source.common.constants import SINGULAR_SOURCE_TITLE
from plugins.bot.handlers.source.common.utils import get_source_menu_text
from plugins.bot.menu import Menu

DETAIL_SOURCE_PATH = "/s/{source_id}/"


@router.page(path=DETAIL_SOURCE_PATH.format(source_id=r"-\d+"))
async def detail_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    if menu.is_admin_user():
        menu.add_button.row_edit_delete()

    menu.add_button.messages_histories()
    menu.add_button.filters(source_id=source_obj.id)
    menu.add_button.statistics()
    if source_obj.is_rewrite:
        menu.add_button.cleanups(amount=len(source_obj.cleanup_list))

    return await get_source_menu_text(
        title=SINGULAR_SOURCE_TITLE,
        source_id=source_id,
        category_id=source_obj.category_id,
        alias=source_obj.title_alias,
        is_rewrite=source_obj.is_rewrite,
    )
