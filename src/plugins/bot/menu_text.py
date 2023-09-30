from collections.abc import Iterable

from plugins.bot.constants.text import (
    MENU_TEXT_CONTENT,
    MENU_TEXT_PARAM,
    MENU_TEXT_QUESTION,
    MENU_TEXT_TITLE,
)


def get_menu_text(
    title: str,
    params: Iterable[tuple[str, str]] = None,
    content: str = None,
    question: str = None,
) -> str:
    lines = [MENU_TEXT_TITLE.format(title)]

    for name, value in params or ():
        lines.append(MENU_TEXT_PARAM.format(name, value))

    if content:
        lines.append(MENU_TEXT_CONTENT.format(content))

    if question:
        lines.append(MENU_TEXT_QUESTION.format(question))

    return "\n".join(lines)
