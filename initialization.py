from pyrogram import Client

from models import db, Category, Source, Filter, Admin
from settings import API_ID, API_HASH, DEVELOP_MODE, BOT_TOKEN

db.create_tables(
    [
        Category, Source, Filter, Admin
    ]
)

user_plugins = dict(
    root='plugins.user',
    exclude=['news_forwarding', ] if DEVELOP_MODE else []
)
user = Client(
    'user', API_ID, API_HASH,
    plugins=user_plugins
)

bot_plugins = dict(
    root='plugins.bot',
    exclude=['news_forwarding', ] if DEVELOP_MODE else []
)
bot = Client(
    'bot', API_ID, API_HASH, bot_token=BOT_TOKEN,
    plugins=bot_plugins
)
