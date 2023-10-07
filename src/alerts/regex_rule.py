import json
import re
from re import Match

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from alerts.configs import AlertRegexHistory
from clients import bot_client
from common.text import get_words
from models import AlertHistory, AlertRule
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_RULE_DETAIL_PATH,
    SINGULAR_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.category.message import (
    GET_CATEGORY_MESSAGE_BUTTON_TEXT,
    GET_CATEGORY_MESSAGE_PATH,
)
from plugins.bot.utils.links import get_channel_formatted_link

FIRING_COUNTER_ALERT_RULE_TEXT = (
    "**В категории {category_link} опубликовано сообщение, подходящее "
    "под паттерн `{pattern}`:**\n\n{message_text}"
)
NUMBER_OF_WORDS = 20


async def check_message_by_regex_alert_rule(
    category_id: int,
    message: Message,
):
    if not (message.text or message.caption):
        return

    text = str(message.text or message.caption)

    for alert_rule in AlertRule.select().where(
        ((AlertRule.category_id == category_id) | (AlertRule.category_id.is_null()))
        & (AlertRule.type == "regex")
    ):
        match = None
        pattern = alert_rule.config["regex"]
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            break

        if not match:
            continue

        await bot_client.send_message(
            chat_id=alert_rule.user_id,
            text=FIRING_COUNTER_ALERT_RULE_TEXT.format(
                category_link=await get_channel_formatted_link(category_id),
                pattern=pattern,
                message_text=_get_short_text(
                    text=text,
                    match=match,
                    message_link=message.link,
                ),
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=SINGULAR_ALERT_RULE_TITLE,
                            callback_data=ALERT_RULE_DETAIL_PATH.format(
                                rule_id=alert_rule.id,
                            )
                            + "?new",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text=GET_CATEGORY_MESSAGE_BUTTON_TEXT,
                            callback_data=GET_CATEGORY_MESSAGE_PATH.format(
                                category_id=category_id,
                                message_id=message.id,
                            ),
                        )
                    ],
                ]
            ),
            disable_web_page_preview=True,
        )
        AlertHistory.create(
            category_id=category_id,
            data=AlertRegexHistory(
                type=alert_rule.type,
                user_id=alert_rule.user_id,
                message=json.loads(message.__str__()),
                match_text=match[0],
                **alert_rule.config,
            ),
            alert_rule_id=alert_rule.id,
        )


def _get_short_text(text: str, match: Match, message_link: str):
    before_words = get_words(text[: match.start()], -1)
    before_text = " ".join(before_words[-NUMBER_OF_WORDS:])

    after_words = get_words(text[match.end() :], 0)
    after_text = " ".join(after_words[:NUMBER_OF_WORDS]).rstrip(".,:;?!")

    return (
        ("…" if len(before_words) > NUMBER_OF_WORDS else "")
        + f"{before_text} -->{match[0]}<-- {after_text}"
        + ("…" if len(after_words) > NUMBER_OF_WORDS else "")
        + f" **[>>>]({message_link})**"
    )
