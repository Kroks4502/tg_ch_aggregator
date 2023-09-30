from models import Filter
from plugins.bot import router
from plugins.bot.handlers.filter.common.constants import (
    QUESTION_CONF_DEL,
    SINGULAR_COMMON_FILTER_TITLE,
    SINGULAR_FILTER_TITLE,
    SUCCESS_FILTER_PATTERN_DEL_TEXT,
)
from plugins.bot.handlers.filter.common.utils import (
    get_filter_menu_success_text,
    get_filter_menu_text,
)
from plugins.bot.menu import Menu


@router.page(path=r"/f/\d+/:delete/")
async def filter_deletion_confirmation(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    menu.add_button.confirmation_delete()

    return await get_filter_menu_text(
        title=SINGULAR_FILTER_TITLE,
        title_common=SINGULAR_COMMON_FILTER_TITLE,
        source_id=filter_obj.source_id,
        filter_type_id=filter_obj.type,
        pattern=filter_obj.pattern,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/f/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    filter_obj.delete_instance()

    return await get_filter_menu_success_text(
        filter_obj=filter_obj,
        action=SUCCESS_FILTER_PATTERN_DEL_TEXT.format(filter_obj.pattern),
    )
