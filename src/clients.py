from telethon import TelegramClient

import settings

user_client: TelegramClient = TelegramClient(
    session=str(settings.SESSIONS_DIR / "user"),
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
    connection_retries=None,
    auto_reconnect=True,
    device_model=settings.DEVICE_MODEL,
    system_version=settings.SYSTEM_VERSION,
    app_version=settings.APP_VERSION,
).start()

bot_client: TelegramClient = TelegramClient(
    session=str(settings.SESSIONS_DIR / "bot"),
    api_id=settings.API_ID,
    api_hash=settings.API_HASH,
).start(bot_token=settings.BOT_TOKEN)
