import logging

from async_lru import alru_cache
from pyrogram.errors import RPCError

from clients import user_client


@alru_cache(maxsize=16)
async def get_user_formatted_link(chat_id: int) -> str:
    """Получить отформатированную в markdown ссылку на пользователя по chat_id."""
    try:
        chat = await user_client.get_chat(chat_id)
        if chat.username:
            return f"[{chat.username}](https://{chat.username}.t.me)"
        full_name = (
            f'{chat.first_name + " " if chat.first_name else ""}'
            f'{chat.last_name + " " if chat.last_name else ""}'
        )
        if full_name:
            return f'{full_name + " " if full_name else ""}…{str(chat_id)[-5:]}'
    except RPCError as e:
        logging.warning(e, exc_info=True)
    return str(chat_id)


@alru_cache(maxsize=256)
async def get_channel_formatted_link(chat_id: int) -> str:
    """Получить отформатированную в markdown ссылку на канал по chat_id."""
    try:
        chat = await user_client.get_chat(chat_id)
        if chat.username:
            return f"[{chat.title}](https://{chat.username}.t.me)"
        if chat.invite_link:
            return f"[{chat.title}]({chat.invite_link})"
        return chat.title
    except RPCError as e:
        logging.warning(e, exc_info=True)
    return str(chat_id)
