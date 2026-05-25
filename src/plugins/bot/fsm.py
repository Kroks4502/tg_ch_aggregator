from aiogram.fsm.state import State, StatesGroup


class WaitInput(StatesGroup):
    """Состояние ожидания текстового ввода после нажатия inline-кнопки."""

    waiting_text = State()
