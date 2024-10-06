from models import Source
from plugins.bot import router
from plugins.bot.constants.text import QUESTION_EDIT_PAGE
from plugins.bot.handlers.source.common.constants import SINGULAR_SOURCE_TITLE
from plugins.bot.handlers.source.common.utils import get_source_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/s/-\d+/:edit/")
async def edit_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(
        id=source_id,
        is_deleted=False,
    )

    menu.add_row_button("Категорию", "nc")
    menu.add_row_button("Псевдоним", "alias")
    menu.add_row_button(
        "Режим",
        ":off_rewrite" if source_obj.is_rewrite else ":on_rewrite",
    )

    return await get_source_menu_text(
        title=SINGULAR_SOURCE_TITLE,
        source_id=source_id,
        category_id=source_obj.category_id,
        alias=source_obj.title_alias,
        is_rewrite=source_obj.is_rewrite,
        question=QUESTION_EDIT_PAGE,
    )
