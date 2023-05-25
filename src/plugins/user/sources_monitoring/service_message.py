from pyrogram import Client, filters
from pyrogram.types import Message

from plugins.user.utils import custom_filters


@Client.on_message(
    custom_filters.monitored_channels & filters.service,
)
async def service_message(client: Client, message: Message):
    await client.read_chat_history(message.chat.id)
