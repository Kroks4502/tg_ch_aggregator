from plugins.bot import menu_params as g_params
from plugins.bot.constants.text import DIALOG, SUCCESS_TEXT
from plugins.bot.handlers.source.common import params
from plugins.bot.handlers.source.common.constants import (
    SINGULAR_SOURCE_TEXT,
    SINGULAR_SOURCE_TITLE,
    SOURCE_TEXT,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link


async def get_source_menu_text(
    title: str,
    source_id: int = None,
    category_id: int = None,
    alias: str = None,
    is_rewrite: bool = None,
    question: str = "",
):
    text_params = []

    if category_id:
        text_params.append(await g_params.category(category_id))

    if alias:
        text_params.append(params.alias(alias))

    if is_rewrite is not None:
        text_params.append(params.rewrite(is_rewrite))

    if source_id:
        source_link = await get_channel_formatted_link(source_id)
        title = f"{title} {source_link}"

    return get_menu_text(
        title=title,
        params=text_params,
        question=question,
    )


async def get_dialog_text(
    doing: str,
    action: str,
    category_id: int = None,
    source_id: int = None,
):
    category_text = ""
    if category_id:
        category_link = await get_channel_formatted_link(category_id)
        category_text = f"категории {category_link}"

    source_text = SINGULAR_SOURCE_TEXT
    if source_id:
        source_link = await get_channel_formatted_link(source_id)
        source_text = f"{SOURCE_TEXT} {source_link}"

    return DIALOG.format(
        doing=f"{doing} {source_text} {category_text}",
        action=action,
    )


async def get_source_menu_success_text(
    source_id: int,
    action: str,
) -> str:
    if source_id:
        source_link = await get_channel_formatted_link(source_id)
        title = f"{SINGULAR_SOURCE_TITLE} {source_link}"
    else:
        title = SINGULAR_SOURCE_TITLE

    return SUCCESS_TEXT.format(text=f"{title} {action}")
