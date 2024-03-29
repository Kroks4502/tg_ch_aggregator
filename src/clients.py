from pyrogram import Client

from settings import API_HASH, API_ID, BOT_TOKEN, SESSIONS_DIR

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

user_client = Client(
    "user",
    API_ID,
    API_HASH,
    plugins=dict(
        root="plugins.user",
    ),
    workdir=SESSIONS_DIR,
)

bot_client = Client(
    "bot",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(
        root="plugins.bot",
    ),
    workdir=SESSIONS_DIR,
)
