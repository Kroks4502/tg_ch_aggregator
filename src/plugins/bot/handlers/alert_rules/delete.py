from alerts.common import get_alert_rule_title
from alerts.counter_rule import remove_evaluation_counter_rule_job
from models import AlertRule
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from scheduler import scheduler


@router.page(path=r"/r/\d+/:delete/")
async def confirmation_delete_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        alert_rule_obj=rule_obj,
        last_text=CONF_DEL_TEXT_TPL.format("правило уведомления"),
    )


@router.page(path=r"/r/\d+/:delete/:y/", back_step=3)
async def delete_alert_rule(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    rule_obj.delete_instance()

    if rule_obj.type == "counter":
        remove_evaluation_counter_rule_job(scheduler=scheduler, alert_rule_obj=rule_obj)

    return (
        f"✅ Правило уведомления **{get_alert_rule_title(alert_rule=rule_obj)}**"
        " удалено"
    )
