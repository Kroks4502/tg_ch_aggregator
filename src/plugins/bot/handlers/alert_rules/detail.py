from peewee import DoesNotExist

from alerts.configs import AlertCounterConfig
from models import AlertHistory, AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    LAST_FIRED_TEXT,
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text
from plugins.bot.handlers.alert_rules.counter_messages import (
    ALERT_COUNTER_MESSAGES_PATH,
)
from plugins.bot.handlers.category.message import GET_CATEGORY_MESSAGE_PATH
from plugins.bot.menu import Menu

DETAIL_ALERT_RULE_PATH = "/r/{rule_id}/"


@router.page(path=DETAIL_ALERT_RULE_PATH.format(rule_id=r"\d+"))
async def detail_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    try:
        history_obj = rule_obj.history.order_by(AlertHistory.id.desc()).get()
    except DoesNotExist:
        history_obj = None

    last_fired_button_data = None
    if rule_obj.type == "regex":
        menu.add_button.edit()
        if (
            history_obj
            and (fired_message := history_obj.data.get("message"))
            and (message_id := fired_message.get("id"))
            and (chat := fired_message.get("chat"))
            and (category_id := chat.get("id"))
        ):
            last_fired_button_data = GET_CATEGORY_MESSAGE_PATH.format(
                category_id=category_id,
                message_id=message_id,
            )
    elif rule_obj.type == "counter" and history_obj:
        config = AlertCounterConfig(**rule_obj.config)
        end_ts = int(history_obj.fired_at.timestamp())
        start_ts = end_ts - config.count_interval * 60
        last_fired_button_data = ALERT_COUNTER_MESSAGES_PATH.format(
            rule_id=rule_obj.id,
            start_ts=start_ts,
            end_ts=end_ts,
        )

    menu.add_button.delete()

    if last_fired_button_data:
        menu.add_row_button(
            LAST_FIRED_TEXT,
            last_fired_button_data,
            new=True,
        )

    return await get_alert_rule_menu_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        rule_type=rule_obj.type,
        **rule_obj.config,
    )
