from pyrogram.types import Message

from alerts.configs import AlertRegexHistory, MatchData
from common.text import get_words
from models import AlertHistory
from plugins.bot import Menu
from plugins.bot.constants.settings import FORMAT_TIMESTAMP
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_RULE_DETAIL_PATH,
    SINGULAR_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.category.message import (
    GET_CATEGORY_MESSAGE_BUTTON_TEXT,
    GET_CATEGORY_MESSAGE_PATH,
)
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link

FIRING_REGEX_ALERT_RULE_TITLE = (
    "В категории {category_link} опубликовано сообщение, подходящее "
    "под паттерн `{pattern}`"
)
NUMBER_OF_WORDS = 20


async def get_alert_regex_message(
    menu: Menu,
    alert_obj: AlertHistory,
    firing_right_now: bool,
):
    alert_data = AlertRegexHistory(**alert_obj.data)

    if "_" not in alert_data.message:
        return ""
    alert_data.message.pop("_")
    message = Message(**alert_data.message)

    menu.add_row_button(
        text=GET_CATEGORY_MESSAGE_BUTTON_TEXT,
        path=GET_CATEGORY_MESSAGE_PATH.format(
            category_id=alert_obj.category_id,
            message_id=message.id,
        ),
    )

    title = FIRING_REGEX_ALERT_RULE_TITLE.format(
        category_link=await get_channel_formatted_link(alert_obj.category_id),
        pattern=alert_data.regex,
    )
    if firing_right_now:
        menu.add_row_button(
            text=SINGULAR_ALERT_RULE_TITLE,
            path=ALERT_RULE_DETAIL_PATH.format(rule_id=alert_obj.alert_rule_id),
            new=True,
        )
        menu.set_footer_buttons = False
    else:
        title = f"__{alert_obj.fired_at.strftime(FORMAT_TIMESTAMP)}__\n\n{title}"

    match_data = MatchData(**alert_data.match)
    return get_menu_text(
        title=title,
        content=_get_short_text(
            text=message.text or message.caption,
            match_text=match_data.text,
            match_start=match_data.start,
            match_end=match_data.end,
        ),
    )


def _get_short_text(text: str, match_text: str, match_start: int, match_end: int):
    before_words = get_words(text[:match_start], -1)
    before_text = " ".join(before_words[-NUMBER_OF_WORDS:])

    after_words = get_words(text[match_end:], 0)
    after_text = " ".join(after_words[:NUMBER_OF_WORDS]).rstrip(".,:;?!")

    return (
        ("…" if len(before_words) > NUMBER_OF_WORDS else "")
        + f"{before_text} -->{match_text}<-- {after_text}"
        + ("…" if len(after_words) > NUMBER_OF_WORDS else "")
    )
