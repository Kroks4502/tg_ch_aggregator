from models import AlertHistory
from plugins.bot import router
from plugins.bot.handlers.alert_rules.alert.alert_counter import (
    get_alert_counter_messages,
)
from plugins.bot.handlers.alert_rules.alert.alert_regex import get_alert_regex_message
from plugins.bot.handlers.alert_rules.common.constants import ALERT_DETAIL_PATH
from plugins.bot.menu import Menu


@router.page(
    path=ALERT_DETAIL_PATH.format(
        alert_id=r"\d+",
    ),
    pagination=True,
)
async def alert_detail(menu: Menu):
    alert_id = menu.path.get_value("a")
    alert_obj: AlertHistory = AlertHistory.get(alert_id)

    firing_right_now = not bool(menu.path.get_value("r"))
    rule_type = alert_obj.alert_rule.type

    if rule_type == "counter":
        return await get_alert_counter_messages(
            menu=menu,
            alert_obj=alert_obj,
            firing_right_now=firing_right_now,
        )

    if rule_type == "regex":
        return await get_alert_regex_message(
            menu=menu,
            alert_obj=alert_obj,
            firing_right_now=firing_right_now,
        )

    return ""
