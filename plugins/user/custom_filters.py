from pyrogram import filters

from initialization import MONITORED_CHANNELS_ID


async def is_forward_from_chat(_, __, message):
    return message.forward_from_chat is not None


forward_from_chat = filters.create(is_forward_from_chat)


async def is_monitored_channels(_, __, message):
    return message.chat.id in MONITORED_CHANNELS_ID


monitored_channels = filters.create(is_monitored_channels)
