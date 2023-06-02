from pyrogram import filters

from models import Source


async def is_forward_from_chat(_, __, message):
    return message.forward_from_chat is not None


forward_from_chat = filters.create(is_forward_from_chat)


async def is_monitored_channels(_, __, message):
    if message.chat:
        return message.chat.id in Source.get_cache_monitored_channels()
    # Может прилететь message без чата
    return False


monitored_channels = filters.create(is_monitored_channels)
