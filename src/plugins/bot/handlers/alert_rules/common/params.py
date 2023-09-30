from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_RULE_COUNTER,
    ALERT_RULE_REGEX,
)

TYPE_COUNTER = "Тип", ALERT_RULE_COUNTER
TYPE_REGEX = "Тип", ALERT_RULE_REGEX


def job_interval(value: int):
    return "Интервал проверки", f"{value} мин."


def count_interval(value: int):
    return "Интервал сообщений", f"{value} мин."


def threshold(value: int):
    return "Порог", f"{value} шт."


def regex(value: str):
    return "Паттерн", f"`{value}`"
