from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from alerts.configs import AlertCounterConfig, AlertRegexConfig
from models import AlertRule
from plugins.bot.utils.menu import Menu

RULE_TYPE_TMPL = "Тип: **{}**"
RULE_COUNTER_JOB_INTERVAL_TMPL = "Интервал проверки правила: **{}** мин."
RULE_COUNTER_COUNT_INTERVAL_TMPL = "Интервал сообщений: **{}** мин."
RULE_COUNTER_THRESHOLD_TMPL = "Порог: **{}** шт."
RULE_REGEX_TMPL = "Паттерн: `{}`"


@Client.on_callback_query(
    filters.regex(r"/r/\d+/(\?new|)$"),
)
async def detail_alert_rule(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    last_text = ""
    if rule_obj.type == "counter":
        config = AlertCounterConfig(**rule_obj.config)

        last_text = (
            f"{RULE_TYPE_TMPL.format('Счётчик сообщений')}\n"
            f"{RULE_COUNTER_JOB_INTERVAL_TMPL.format(config.job_interval)}\n"
            f"{RULE_COUNTER_COUNT_INTERVAL_TMPL.format(config.count_interval)}\n"
            f"{RULE_COUNTER_THRESHOLD_TMPL.format(config.threshold)}"
        )

    elif rule_obj.type == "regex":
        config = AlertRegexConfig(**rule_obj.config)
        last_text = (
            f"{RULE_TYPE_TMPL.format('Регулярное выражение')}\n"
            f"{RULE_REGEX_TMPL.format(config.regex)}\n"
        )

    menu.add_row_button("Удалить", ":delete")

    text = await menu.get_text(alert_rule_obj=rule_obj, last_text=last_text)

    if menu.need_send_new_message:
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=text,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        return

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
