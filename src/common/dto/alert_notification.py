from dataclasses import dataclass


@dataclass(frozen=True)
class AlertNotification:
    """Сработавший alert — бот сам подтянет содержимое по alert_id."""

    alert_id: int
    user_id: int
