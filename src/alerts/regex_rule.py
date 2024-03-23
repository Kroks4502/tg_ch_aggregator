import json
import re

from telethon.tl.custom import Message

from alerts.configs import AlertRegexHistory, MatchData
from common.call_handlers import call_callback_query_handler
from models import AlertHistory, AlertRule
from plugins.bot.handlers.alert_rules.alert.detail import alert_detail
from plugins.bot.handlers.alert_rules.common.constants import ALERT_DETAIL_PATH


async def check_message_by_regex_alert_rule(
    category_id: int,
    message: Message,
):
    if not message.text:
        return

    for rule_obj in AlertRule.select().where(
        ((AlertRule.category_id == category_id) | (AlertRule.category_id.is_null()))
        & (AlertRule.type == "regex")
    ):
        match = None
        pattern = rule_obj.config["regex"]
        for match in re.finditer(pattern, message.text, flags=re.IGNORECASE):
            break

        if not match:
            continue

        alert_obj = AlertHistory.create(
            category_id=category_id,
            data=AlertRegexHistory(
                type=rule_obj.type,
                user_id=rule_obj.user_id,
                message=json.loads(message.__str__()),
                match=MatchData(
                    text=match[0],
                    start=match.start(),
                    end=match.end(),
                ),
                **rule_obj.config,
            ),
            alert_rule_id=rule_obj.id,
        )

        await call_callback_query_handler(
            func=alert_detail,
            user_id=rule_obj.user_id,
            path=(
                ALERT_DETAIL_PATH.format(
                    alert_id=alert_obj.id,
                )
                + "?new"
            ),
        )
