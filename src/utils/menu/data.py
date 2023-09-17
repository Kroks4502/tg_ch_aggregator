from dataclasses import dataclass


@dataclass
class ButtonData:
    """
    - title: Название кнопки (обязательно).
    - path: Относительный путь до объекта (обязательно).
    - amount: Количество объектов.
    """

    title: str
    path: str | int
    amount: str | int = None

    def __post_init__(self):
        self.path = str(self.path)

    def get_processed_title(self, length: int = None, amount: str | int = None):
        title = self.title

        if length and len(self.title) > length:
            title = self.title[:length].rstrip(" ") + "…"

        amount = amount or self.amount
        if amount:
            return f"{title} ({amount})"

        return title
