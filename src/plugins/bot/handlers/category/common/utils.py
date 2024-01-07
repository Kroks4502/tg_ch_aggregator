from plugins.bot.constants.text import DIALOG, SUCCESS_TEXT
from plugins.bot.handlers.category.common import params
from plugins.bot.handlers.category.common.constants import (
    CATEGORY_TEXT,
    PLURAL_CATEGORY_TITLE,
    SINGULAR_CATEGORY_TITLE,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link


async def get_category_menu_text(
    category_id: int = None,
    desc: str = None,
    question: str = "",
):
    text_params = []

    if desc:
        text_params.append(params.description(desc))

    if category_id:
        category_link = await get_channel_formatted_link(category_id)
        title = f"{SINGULAR_CATEGORY_TITLE} {category_link}"
    else:
        title = PLURAL_CATEGORY_TITLE

    return get_menu_text(
        title=title,
        params=text_params,
        question=question,
    )


async def get_edit_dialog_text(
    category_id: int,
    doing: str,
    action: str,
):
    category_link = await get_channel_formatted_link(category_id)
    return DIALOG.format(
        doing=f"{doing} {CATEGORY_TEXT.format(category_link)}",
        action=action,
    )


async def get_category_menu_success_text(
    category_id: int,
    action: str,
) -> str:
    category_link = await get_channel_formatted_link(category_id)
    return SUCCESS_TEXT.format(
        text=f"{SINGULAR_CATEGORY_TITLE} {category_link} {action}"
    )
