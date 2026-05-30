from typing import Protocol


class UserErrorNotifier(Protocol):
    """Отправка сообщения об ошибке userbot'а администраторам."""

    async def report(self, text: str) -> None:
        pass
