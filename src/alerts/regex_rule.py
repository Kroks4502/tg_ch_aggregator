import json
import re

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from clients import bot_client
from common import get_words
from models import AlertHistory, AlertRule

MSG_TEXT_TMPL = "Новое сообщение подходящее под паттерн `{pattern}`:\n\n{message}"
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

        match_text = match[0]

        await bot_client.send_message(
            chat_id=alert_rule.user_id,
            text=MSG_TEXT_TMPL.format(
                pattern=pattern,
                message=(
                    f"…{' '.join(get_words(text[: match.start()], -1)[-NUMBER_OF_WORDS:])} -->{match_text}<--"
                    f" {' '.join(get_words(text[match.end():], 0)[:NUMBER_OF_WORDS]).rstrip('.,:;?!')}…"
                    f" **[>>>]({message.link})**"
                ),
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Правило уведомления",
                            callback_data=f"/c/{category_id}/r/{alert_rule.id}/?new",
                        )
                    ]
                ]
            ),
            disable_web_page_preview=True,
        )
        AlertHistory.create(
            category_id=category_id,
            data=dict(
                type="regex",
                user_id=alert_rule.user_id,
                regex=pattern,
                message=json.loads(message.__str__()),
                match_text=match_text,
            ),
        )
