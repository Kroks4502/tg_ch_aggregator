from alerts.configs import AlertCounterConfig, AlertRegexConfig
from models import AlertRule
from plugins.bot import router
from plugins.bot.menu import Menu

RULE_TYPE_TMPL = "Тип: **{}**"
RULE_COUNTER_JOB_INTERVAL_TMPL = "Интервал проверки правила: **{}** мин."
RULE_COUNTER_COUNT_INTERVAL_TMPL = "Интервал сообщений: **{}** мин."
RULE_COUNTER_THRESHOLD_TMPL = "Порог: **{}** шт."
RULE_REGEX_TMPL = "Паттерн: `{}`"


@router.page(path=r"/r/\d+/")
async def detail_alert_rule(menu: Menu):
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
        menu.add_button.edit()

    menu.add_button.delete()

    return await menu.get_text(alert_rule_obj=rule_obj, last_text=last_text)
