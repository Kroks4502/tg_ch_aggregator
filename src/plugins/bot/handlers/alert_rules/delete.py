from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from alerts.common import get_alert_rule_title
from alerts.counter_rule import remove_evaluation_counter_rule_job
from models import AlertRule
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from scheduler import scheduler


@Client.on_callback_query(
    filters.regex(r"/r/\d+/:delete/$") & custom_filters.admin_only,
)
async def confirmation_delete_alert_rule(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    menu.add_button.confirmation_delete()

    text = await menu.get_text(
        alert_rule_obj=rule_obj,
        last_text=CONF_DEL_TEXT_TPL.format("правило уведомления"),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/r/\d+/:delete/:y/$"),
)
async def delete_alert_rule(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    rule_obj.delete_instance()

    if rule_obj.type == "counter":
        remove_evaluation_counter_rule_job(scheduler=scheduler, alert_rule_obj=rule_obj)

    text = (
        f"✅ Правило уведомления **{get_alert_rule_title(alert_rule=rule_obj)}**"
        " удалено"
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
