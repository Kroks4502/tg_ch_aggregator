from pyrogram.types import Message

from alerts.configs import AlertRegexConfig
from models import AlertRule
from plugins.bot import router, validators
from plugins.bot.handlers.alert_rules.common.constants import (
    ACTION_ENTER_REGEX,
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import (
    get_alert_rule_menu_success_text,
    get_dialog_text,
)
from plugins.bot.menu import Menu


@router.wait_input()
async def edit_regex_alert_rule_waiting_input(
    message: Message,
    menu: Menu,
):
    rule_id = menu.path.get_value("r")
    rule_obj = AlertRule.get(rule_id)

    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    old_pattern = rule_obj.config["regex"]
    rule_obj.config["regex"] = pattern
    rule_obj.save()

    return await get_alert_rule_menu_success_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        rule_obj=rule_obj,
        action=f"изменено (старый паттерн `{old_pattern}`)",
    )


@router.page(
    path=r"/r/\d+/:edit/",
    reply=True,
    add_wait_for_input=edit_regex_alert_rule_waiting_input,
)
async def edit_regex_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)
    config = AlertRegexConfig(**rule_obj.config)
    return await get_dialog_text(
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        doing="изменяешь",
        action=ACTION_ENTER_REGEX,
        pattern=config.regex,
    )
