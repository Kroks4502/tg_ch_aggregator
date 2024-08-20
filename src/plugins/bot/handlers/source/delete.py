from models import Source
from plugins.bot import router
from plugins.bot.handlers.source.common.constants import (
    QUESTION_CONF_DEL,
    SINGULAR_SOURCE_TITLE,
)
from plugins.bot.handlers.source.common.utils import (
    get_source_menu_success_text,
    get_source_menu_text,
)
from plugins.bot.menu import Menu


@router.page(path=r"/s/-\d+/:delete/")
async def source_deletion_confirmation(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(
        id=source_id,
        is_deleted=False,
    )

    menu.add_button.confirmation_delete()

    return await get_source_menu_text(
        title=SINGULAR_SOURCE_TITLE,
        source_id=source_id,
        category_id=source_obj.category_id,
        alias=source_obj.title_alias,
        is_rewrite=source_obj.is_rewrite,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/s/-\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(id=source_id, is_deleted=False)

    source_obj.is_deleted = True
    source_obj.save()

    return await get_source_menu_success_text(source_id=source_id, action="удален")
