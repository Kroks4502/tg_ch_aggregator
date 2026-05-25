"""
Реестр функций-обработчиков пользовательского ввода (replacement for
InputWaitManager). Функции непиклабельны, поэтому в FSM-data сохраняется
только строковый ключ, а сама функция тянется отсюда.
"""

from typing import Awaitable, Callable

_REGISTRY: dict[str, Callable[..., Awaitable]] = {}


def make_key(func: Callable) -> str:
    return f"{func.__module__}.{func.__qualname__}"


def register(func: Callable[..., Awaitable]) -> str:
    key = make_key(func)
    _REGISTRY[key] = func
    return key


def resolve(key: str) -> Callable[..., Awaitable] | None:
    return _REGISTRY.get(key)
