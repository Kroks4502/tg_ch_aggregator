import logging

from async_lru import alru_cache
from telethon.tl.functions.channels import GetFullChannelRequest

from clients import telethon_user_client


@alru_cache(maxsize=16)
async def get_user_formatted_link(chat_id: int) -> str:
    """Получить отформатированную ссылку на пользователя по chat_id."""
    try:
        entity = await telethon_user_client.get_entity(chat_id)
        username = getattr(entity, "username", None)
        if username:
            return f"[{username}](https://{username}.t.me)"
        first = getattr(entity, "first_name", "") or ""
        last = getattr(entity, "last_name", "") or ""
        full_name = f"{first} {last}".strip()
        if full_name:
            return f"{full_name} …{str(chat_id)[-5:]}"
    except Exception as e:
        logging.warning("get_user_formatted_link(%s): %s", chat_id, e)
    return str(chat_id)


@alru_cache(maxsize=256)
async def get_channel_formatted_link(chat_id: int) -> str:
    """Получить отформатированную ссылку на канал по chat_id."""
    try:
        entity = await telethon_user_client.get_entity(chat_id)
        title = getattr(entity, "title", None) or str(chat_id)
        username = getattr(entity, "username", None)
        if username:
            return f"[{title}](https://{username}.t.me)"
        # Для закрытых каналов получаем invite link
        try:
            full = await telethon_user_client(GetFullChannelRequest(entity))
            invite_link = getattr(full.full_chat, "invite_link", None)
            if invite_link:
                return f"[{title}]({invite_link})"
        except Exception:
            pass
        return title
    except Exception as e:
        logging.warning("get_channel_formatted_link(%s): %s", chat_id, e)
    return str(chat_id)
