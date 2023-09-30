from plugins.bot import Menu, router
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_RULE_COUNTER,
    ALERT_RULE_REGEX,
    NEW_ALERT_RULE_TITLE,
    NEW_COMMON_ALERT_RULE_TITLE,
    QUESTION_SELECT_ALERT_RULE_TYPE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text


@router.page(path=r"/r/:add/")
async def add_alert_rule(menu: Menu):
    menu.add_row_button(ALERT_RULE_COUNTER, "counter")
    menu.add_row_button(ALERT_RULE_REGEX, "regex")

    category_id = menu.path.get_value("c")

    return await get_alert_rule_menu_text(
        title=NEW_ALERT_RULE_TITLE,
        title_common=NEW_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=category_id,
        question=QUESTION_SELECT_ALERT_RULE_TYPE,
    )
