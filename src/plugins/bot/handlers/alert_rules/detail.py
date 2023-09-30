from models import AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/r/\d+/")
async def detail_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    if rule_obj.type == "regex":
        menu.add_button.edit()

    menu.add_button.delete()

    return await get_alert_rule_menu_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        rule_type=rule_obj.type,
        **rule_obj.config,
    )
