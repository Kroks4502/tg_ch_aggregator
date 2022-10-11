from pyrogram import Client

from settings import API_ID, API_HASH, BOT_TOKEN

user = Client(
    'user', API_ID, API_HASH,
    plugins=dict(root='plugins.user',),
    device_model='Test stand'
)

bot = Client(
    'bot', API_ID, API_HASH, bot_token=BOT_TOKEN,
    plugins=dict(root='plugins.bot',)
)
