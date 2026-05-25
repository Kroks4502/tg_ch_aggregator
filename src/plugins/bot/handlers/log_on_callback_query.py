import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery

from clients import dispatcher


class LogCallbackQueryMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        logging.debug(event.data)
        return await handler(event, data)


dispatcher.callback_query.outer_middleware(LogCallbackQueryMiddleware())
