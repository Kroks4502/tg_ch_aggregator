from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot import menu_params as g_params
from plugins.bot.constants.text import DIALOG, SUCCESS_TEXT
from plugins.bot.handlers.filter.common import params
from plugins.bot.handlers.filter.common.constants import (
    ACTION_ENTER_PATTERN,
    FILTER_PATTERN_TEXT,
    FILTER_TYPE_TEXT,
    SINGULAR_COMMON_FILTER_TEXT,
    SINGULAR_COMMON_FILTER_TITLE,
    SINGULAR_FILTER_TEXT,
    SINGULAR_FILTER_TITLE,
    SOURCE_TEXT,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link


async def get_filter_menu_text(
    title: str,
    title_common: str,
    source_id: int = None,
    filter_type_id: int = None,
    pattern: str = None,
    question: str = "",
):
    text_params = []

    if source_id:
        text_params.append(await g_params.source(source_id))
    else:
        title = title_common

    if filter_type_id:
        text_params.append(params.filter_type(filter_type_id))

    if pattern:
        text_params.append(params.pattern(pattern))

    return get_menu_text(
        title=title,
        params=text_params,
        question=question,
    )


async def get_dialog_enter_pattern_text(
    filter_type_id: int,
    source_id: int | None,
    action: str,
    pattern: str = None,
):
    text = SINGULAR_COMMON_FILTER_TEXT
    if source_id:
        source_link = await get_channel_formatted_link(source_id)
        text = f"{SINGULAR_FILTER_TEXT} {SOURCE_TEXT.format(source_link)}"

    pattern_text = ""
    if pattern:
        pattern_text = f" {FILTER_PATTERN_TEXT.format(pattern)}"

    filter_type = FILTER_TYPES_BY_ID.get(filter_type_id)
    return DIALOG.format(
        doing=f"{action} {text} {FILTER_TYPE_TEXT.format(filter_type)}{pattern_text}",
        action=ACTION_ENTER_PATTERN,
    )


async def get_filter_menu_success_text(
    filter_obj: Filter,
    action: str,
) -> str:
    if filter_obj.source_id:
        source_link = await get_channel_formatted_link(filter_obj.source_id)
        text = f"{SINGULAR_FILTER_TITLE} {SOURCE_TEXT.format(source_link)}"
    else:
        text = SINGULAR_COMMON_FILTER_TITLE

    filter_type = FILTER_TYPES_BY_ID.get(filter_obj.type)
    return SUCCESS_TEXT.format(
        text=f"{text} {FILTER_TYPE_TEXT.format(filter_type)} {action}"
    )
