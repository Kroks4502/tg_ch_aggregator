from dataclasses import dataclass

from common.db_json_fields import DBJsonField


@dataclass
class AlertCounterConfig(DBJsonField):
    """
    Конфигурация правила уведомления типа "counter".

    - job_interval: Интервал между проверками.
    - count_interval: Интервал для подсчета количества сообщений.
    - threshold: Порог срабатывания уведомления.
    """

    job_interval: int
    count_interval: int
    threshold: int


@dataclass
class AlertRegexConfig(DBJsonField):
    """
    Конфигурация правила уведомления типа "regex".

    - regex: Регулярное выражение для проверки каждого нового сообщения.
    """

    regex: str


# HISTORY


@dataclass
class AlertHistory(DBJsonField):
    type: str
    user_id: int


@dataclass
class AlertCounterHistory(AlertHistory, AlertCounterConfig):
    actual_amount_messages: int


@dataclass
class MatchData(DBJsonField):
    start: int
    end: int
    text: str


@dataclass
class AlertRegexHistory(AlertHistory, AlertRegexConfig):
    message: dict
    match: MatchData | dict
