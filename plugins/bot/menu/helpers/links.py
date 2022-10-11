from async_lru import alru_cache
from pyrogram.errors import RPCError

from initialization import user
from log import logger


@alru_cache(maxsize=32)
async def get_user_formatted_link(tg_id: int) -> str:
    try:
        chat = await user.get_chat(tg_id)
        if chat.username:
            return f'[{chat.username}](https://{chat.username}.t.me)'
        full_name = (f'{chat.first_name + " " if chat.first_name else ""}'
                     f'{chat.last_name + " " if chat.last_name else ""}')
        if full_name:
            return (f'{full_name} ({tg_id})'
                    if full_name else f'{tg_id}')
    except RPCError as e:
        logger.warning(e, exc_info=True)
    return str(tg_id)


@alru_cache(maxsize=32)
async def get_channel_formatted_link(tg_id: int) -> str:
    try:
        chat = await user.get_chat(tg_id)
        if chat.username:
            return f'[{chat.title}](https://{chat.username}.t.me)'
        if chat.invite_link:
            return f'[{chat.title}]({chat.invite_link})'
        return chat.title
    except RPCError as e:
        logger.warning(e, exc_info=True)
    return str(tg_id)
