from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from async_lru import alru_cache

from models import User


@alru_cache(maxsize=512, ttl=60)
async def _is_admin_cached(user_id: int) -> bool:
    return User.select().where((User.id == user_id) & (User.is_admin == True)).exists()


class AdminOnlyMiddleware(BaseMiddleware):
    """
    Прерывает обработку callback_query от не-админов.
    Сообщения (Message) пропускает без проверки — команды /start и /cancel
    создают пользователя в БД через main_menu_by_command.
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if not await _is_admin_cached(user_id):
                await event.answer(text="⛔️ Доступ только для администраторов")
                return None
        elif isinstance(event, Message):
            pass

        return await handler(event, data)
