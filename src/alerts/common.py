from models import AlertRule


def get_alert_rule_title(alert_rule: AlertRule) -> str:
    """Получить название для правила уведомления."""
    if alert_rule.type == "counter":
        return (
            f"{alert_rule.config.get('job_interval')} / "
            f"{alert_rule.config.get('count_interval')} / "
            f"{alert_rule.config.get('threshold')}"
        )

    if alert_rule.type == "regex":
        return alert_rule.config.get("regex")

    return ""
