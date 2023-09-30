from pyrogram.types import Message

from models import AlertRule
from plugins.bot import router, validators
from plugins.bot.handlers.alert_rules.common.constants import (
    ACTION_ENTER_REGEX,
    NEW_ALERT_RULE_TITLE,
    NEW_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import (
    get_alert_rule_menu_success_text,
    get_dialog_text,
)
from plugins.bot.menu import Menu


@router.wait_input(back_step=2)
async def add_regex_alert_rule_waiting_input(
    message: Message,
    menu: Menu,
):
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    category_id = menu.path.get_value("c")
    rule_obj = AlertRule.create(
        user_id=message.from_user.id,
        category_id=category_id,
        type="regex",
        config=dict(regex=pattern),
    )

    return await get_alert_rule_menu_success_text(
        title=NEW_ALERT_RULE_TITLE,
        title_common=NEW_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        rule_obj=rule_obj,
        action="добавлено",
    )


@router.page(
    path=r"/r/:add/regex/",
    reply=True,
    add_wait_for_input=add_regex_alert_rule_waiting_input,
)
async def add_regex_alert_rule(menu: Menu):
    return await get_dialog_text(
        user_id=menu.user.id,
        category_id=menu.path.get_value("c"),
        doing="добавляешь",
        action=ACTION_ENTER_REGEX,
    )
