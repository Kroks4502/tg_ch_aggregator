from typing import Protocol

from common.dto import AlertNotification


class AlertNotifier(Protocol):
    """Доставка alert-уведомления пользователю, на которого настроено правило."""

    async def alert(self, notification: AlertNotification) -> None:
        pass
