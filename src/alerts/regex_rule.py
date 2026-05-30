import re

from alerts.configs import AlertRegexHistory, MatchData
from common.dto import AlertNotification
from common.notifier_registry import get_alert_notifier
from models import AlertHistory, AlertRule
from plugins.user.utils.telethon_helpers import msg_text, tl_message_to_dict


async def check_message_by_regex_alert_rule(
    category_id: int,
    message,
):
    # Telethon: text покрывает и текст, и подпись медиа
    text = msg_text(message)
    if not text:
        return

    for rule_obj in AlertRule.select().where(
        ((AlertRule.category_id == category_id) | (AlertRule.category_id.is_null()))
        & (AlertRule.type == "regex")
    ):
        match = None
        pattern = rule_obj.config["regex"]
        for match in re.finditer(pattern, str(text), flags=re.IGNORECASE):
            break

        if not match:
            continue

        alert_obj = AlertHistory.create(
            category_id=category_id,
            data=AlertRegexHistory(
                type=rule_obj.type,
                user_id=rule_obj.user_id,
                message=tl_message_to_dict(message),
                match=MatchData(
                    text=match[0],
                    start=match.start(),
                    end=match.end(),
                ),
                **rule_obj.config,
            ),
            alert_rule_id=rule_obj.id,
        )

        await get_alert_notifier().alert(
            AlertNotification(
                alert_id=alert_obj.id,
                user_id=rule_obj.user_id,
            )
        )
