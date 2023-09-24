from pyrogram.types import Message

from models import AlertRule
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
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

    return (
        "✅ Правило уведомления о сообщениях соответствующих регулярному выражению"
        f" изменено c `{old_pattern}` на `{pattern}`"
    )


@router.page(
    path=r"/r/\d+/:edit/",
    reply=True,
    add_wait_for_input=edit_regex_alert_rule_waiting_input,
)
async def edit_regex_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj = AlertRule.get(rule_id)

    return (
        f"ОК. Ты изменяешь правило уведомления `{rule_obj.config['regex']}`.\n\n"
        f"**Введи регулярное выражение** или {CANCEL}"
    )
