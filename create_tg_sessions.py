"""
Создание Telethon-сессии для userbot.

Использование:
    python create_tg_sessions.py

Предварительно удалите старый sessions/user.session (pyrogram-формат),
если он существует: форматы несовместимы.

aiogram-бот работает через BOT_TOKEN — bot.session не нужен.
"""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)


async def create_telethon_sessions():
    """
    Создать userbot-сессию в формате Telethon.

    После этого sessions/user.session будет в Telethon-формате (SQLite).
    aiogram-бот работает через BOT_TOKEN без файла сессии — bot.session не нужен.

    [!] Предварительно удалите старый sessions/user.session (pyrogram-формат),
        если он существует: форматы несовместимы.
    """
    from telethon import TelegramClient

    from settings import API_HASH, API_ID, SESSIONS_DIR

    session_path = SESSIONS_DIR / "user"

    log.info("[user_client / Telethon]: Инициализация userbot-сессии")
    log.info("  Файл сессии: %s.session", session_path)

    async with TelegramClient(str(session_path), API_ID, API_HASH) as client:
        me = await client.get_me()
        log.info("✓ Userbot авторизован: @%s (id=%s)", me.username or "—", me.id)

    log.info("✓ Сессия создана. aiogram-бот использует BOT_TOKEN — bot.session не нужен.")


if __name__ == "__main__":
    asyncio.run(create_telethon_sessions())
