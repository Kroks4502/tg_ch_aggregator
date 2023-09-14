from dataclasses import dataclass


@dataclass
class AlertCounterConfig:
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
class AlertRegexConfig:
    """
    Конфигурация правила уведомления типа "regex".

    - regex: Регулярное выражение для проверки каждого нового сообщения.
    """

    regex: str
