import json
import re

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from clients import bot
from models import AlertHistory, AlertRule

MSG_TEXT_TMPL = (
    "Новое сообщение подходящее под паттерн `{pattern}`:\n\n{text}\n\n{link}"
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
        (AlertRule.category_id == category_id) & (AlertRule.type == "regex")
    ):
        match = None
        pattern = alert_rule.config["regex"]
        for match in re.finditer(pattern, text):
            break

        if not match:
            continue

        match_text = match[0]

        await bot.send_message(
            chat_id=alert_rule.user_id,
            text=MSG_TEXT_TMPL.format(
                pattern=pattern,
                text=(
                    f"…{' '.join(get_words(text[: match.start()], -1)[-NUMBER_OF_WORDS:])} -->{match_text}<--"
                    f" {' '.join(get_words(text[match.end():], 0)[:NUMBER_OF_WORDS])}…"
                ),
                link=message.link,
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


def get_words(text: str, line: int) -> list:
    if (lines := text.splitlines()) and (line := lines[line]):
        return [word for word in line.split(" ") if word != ""]
    return []
