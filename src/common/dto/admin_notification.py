from dataclasses import dataclass, field


@dataclass(frozen=True)
class Button:
    text: str
    callback_data: str


@dataclass(frozen=True)
class ButtonRow:
    buttons: tuple[Button, ...]


@dataclass(frozen=True)
class AdminNotification:
    """Уведомление, доставляемое всем администраторам бота."""

    text: str
    button_rows: tuple[ButtonRow, ...] = field(default_factory=tuple)
    except_user_id: int | None = None
