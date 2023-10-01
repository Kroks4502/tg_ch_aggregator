from alerts.configs import AlertCounterConfig, AlertRegexConfig
from models import AlertRule


def get_alert_rule_title(alert_rule: AlertRule) -> str:
    """Получить название для правила уведомления."""
    if alert_rule.type == "counter":
        config = AlertCounterConfig(**alert_rule.config)
        return f"{config.job_interval} / {config.count_interval} / {config.threshold}"

    if alert_rule.type == "regex":
        config = AlertRegexConfig(**alert_rule.config)
        return config.regex

    return ""
