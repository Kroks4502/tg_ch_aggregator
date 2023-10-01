from typing import Awaitable, Callable

from pyrogram.enums import ChatType
from pyrogram.types import CallbackQuery, Chat, Message, User

from clients import bot_client


async def call_callback_query_handler(
    func: Callable[..., Awaitable],
    user_id: int,
    callback_query_data: str,
):
    from_user = User(id=user_id)
    await func(
        bot_client,
        CallbackQuery(
            client=bot_client,
            id=...,
            from_user=from_user,
            chat_instance=...,
            data=callback_query_data,
            message=Message(
                client=bot_client,
                id=...,
                from_user=from_user,
                chat=Chat(
                    client=bot_client,
                    id=from_user.id,
                    type=ChatType.PRIVATE,
                ),
            ),
        ),
    )
