from typing import Protocol

from common.dto import AdminNotification


class AdminNotifier(Protocol):
    """Доставка произвольного уведомления всем администраторам бота."""

    async def notify(self, notification: AdminNotification) -> None:
        pass
