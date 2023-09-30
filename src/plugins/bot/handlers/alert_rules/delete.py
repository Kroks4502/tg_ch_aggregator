from alerts.counter_rule import remove_evaluation_counter_rule_job
from models import AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    QUESTION_CONF_DEL,
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import (
    get_alert_rule_menu_success_text,
    get_alert_rule_menu_text,
)
from plugins.bot.menu import Menu
from scheduler import scheduler


@router.page(path=r"/r/\d+/:delete/")
async def alert_rule_deletion_confirmation(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    menu.add_button.confirmation_delete()

    return await get_alert_rule_menu_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        rule_type=rule_obj.type,
        **rule_obj.config,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/r/\d+/:delete/:y/", back_step=3)
async def delete_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    rule_obj.delete_instance()

    if rule_obj.type == "counter":
        remove_evaluation_counter_rule_job(scheduler=scheduler, alert_rule_obj=rule_obj)

    return await get_alert_rule_menu_success_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        rule_obj=rule_obj,
        action="удалено",
    )
