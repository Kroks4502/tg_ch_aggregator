from peewee import DoesNotExist

from models import AlertHistory, AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_COUNTER_MESSAGES_PATH,
    ALERT_RULE_DETAIL_PATH,
    LAST_FIRED_TEXT,
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text
from plugins.bot.handlers.category.message import GET_CATEGORY_MESSAGE_PATH
from plugins.bot.menu import Menu


@router.page(path=ALERT_RULE_DETAIL_PATH.format(rule_id=r"\d+"))
async def detail_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    try:
        alert_obj = rule_obj.history.order_by(AlertHistory.id.desc()).get()
    except DoesNotExist:
        alert_obj = None

    if rule_obj.type == "regex":
        menu.add_button.delete()
        menu.add_button.edit()
        if (
            alert_obj
            and (fired_message := alert_obj.data.get("message"))
            and (message_id := fired_message.get("id"))
            and (chat := fired_message.get("chat"))
            and (category_id := chat.get("id"))
        ):
            menu.add_row_button(
                text=LAST_FIRED_TEXT,
                path=GET_CATEGORY_MESSAGE_PATH.format(
                    category_id=category_id,
                    message_id=message_id,
                ),
                new=True,
            )
    elif rule_obj.type == "counter":
        menu.add_button.delete()
        if alert_obj:
            menu.add_row_button(
                text=LAST_FIRED_TEXT,
                path=ALERT_COUNTER_MESSAGES_PATH.format(
                    alert_id=alert_obj.id,
                ).strip("/"),
            )

    return await get_alert_rule_menu_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        rule_type=rule_obj.type,
        **rule_obj.config,
    )
