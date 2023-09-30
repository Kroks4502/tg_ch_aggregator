from plugins.bot import menu_params as g_params
from plugins.bot.constants.text import DIALOG, SUCCESS_TEXT
from plugins.bot.handlers.cleanup.common import params
from plugins.bot.handlers.cleanup.common.constants import (
    ACTION_ENTER_PATTERN,
    SINGULAR_CLEANUP_PATTERN_TEXT,
    SINGULAR_CLEANUP_PATTERN_TITLE,
    SINGULAR_CLEANUP_TITLE,
    SINGULAR_COMMON_CLEANUP_PATTERN_TEXT,
    SINGULAR_COMMON_CLEANUP_PATTERN_TITLE,
    SINGULAR_COMMON_CLEANUP_TITLE,
    SOURCE_TEXT,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link


async def get_cleanup_menu_text(
    source_id: int = None,
    pattern: str = None,
    question: str = "",
):
    text_params = []

    if source_id:
        title = SINGULAR_CLEANUP_TITLE
        text_params.append(await g_params.source(source_id))
    else:
        title = SINGULAR_COMMON_CLEANUP_TITLE

    if pattern:
        text_params.append(params.pattern(pattern))

    return get_menu_text(
        title=title,
        params=text_params,
        question=question,
    )


async def get_dialog_enter_pattern_text(
    source_id: int | None,
    action: str,
    pattern: str = None,
):
    text = SINGULAR_COMMON_CLEANUP_PATTERN_TEXT
    source_text = ""
    if source_id:
        text = SINGULAR_CLEANUP_PATTERN_TEXT
        source_link = await get_channel_formatted_link(source_id)
        source_text = f" {SOURCE_TEXT.format(source_link)}"

    pattern_text = ""
    if pattern:
        pattern_text = f" `{pattern}`"

    return DIALOG.format(
        doing=f"{action} {text}{pattern_text}{source_text}",
        action=ACTION_ENTER_PATTERN,
    )


async def get_cleanup_menu_success_text(
    source_id: int,
    pattern: str,
    action: str,
) -> str:
    if source_id:
        title = SINGULAR_CLEANUP_PATTERN_TITLE
    else:
        title = SINGULAR_COMMON_CLEANUP_PATTERN_TITLE

    source_text = ""
    if source_id:
        source_link = await get_channel_formatted_link(source_id)
        source_text = f" {SOURCE_TEXT.format(source_link)}"

    return SUCCESS_TEXT.format(text=f"{title}{source_text} `{pattern}` {action}")
