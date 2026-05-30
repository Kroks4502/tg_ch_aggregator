"""
Создание сессий Telegram.

Стандартный режим (pyrogram + aiogram-бот):
    python create_tg_sessions.py

Режим Telethon — этап 2 миграции (только userbot-сессия, aiogram не нуждается в сессии):
    python create_tg_sessions.py --telethon

Примечание: при переходе на Telethon (PR-6) старый sessions/user.session
(pyrogram-формат) должен быть удалён перед созданием нового.
"""

import asyncio
import sys

SUCCESS_MESSAGE_TEXT = (
    "Sessions for Telegram user `{user_id}` (`{user_username}`) "
    "and bot `{bot_id}` (`{bot_username}`) are valid"
)


# ---------------------------------------------------------------------------
# Стандартный режим — pyrogram (этап 1 и ниже)
# ---------------------------------------------------------------------------

async def create_pyrogram_sessions():
    """
    Создать pyrogram-сессии для user-client и bot-client.

    [!] Для отправки тестового сообщения бот уже должен быть запущен
        и пользователь должен был с ним общаться ранее.
    """
    from clients import bot_client, user_client  # noqa: E402

    bot_client.plugins = None
    user_client.plugins = None

    print("\033[93m[bot_client]: Initialize Telegram bot client\033[0m")
    async with bot_client:
        print("\033[93m[bot_client]: Get bot info\033[0m")
        bot_info = await bot_client.get_me()
        print(bot_info)

        print("\033[93m[user_client]: Initialize Telegram user client\033[0m")
        async with user_client:
            print("\033[93m[user_client]: Get user info\033[0m")
            user_info = await user_client.get_me()
            print(user_info)

            print("\033[93m[bot_client]: Send message to user_client\033[0m")
            message_text = SUCCESS_MESSAGE_TEXT.format(
                user_id=user_info.id,
                user_username=user_info.username,
                bot_id=bot_info.id,
                bot_username=bot_info.username,
            )
            await bot_client.send_message(
                chat_id=user_info.id,
                text=message_text,
            )
    print(f"\033[92m{message_text}\033[0m")  # noqa: T201


# ---------------------------------------------------------------------------
# Режим Telethon — этап 2 (только userbot-сессия)
# ---------------------------------------------------------------------------

async def create_telethon_sessions():
    """
    Создать userbot-сессию в формате Telethon.

    После этого sessions/user.session будет в Telethon-формате (SQLite).
    aiogram-бот работает через BOT_TOKEN без файла сессии — bot.session не нужен.

    [!] Предварительно удалите старый sessions/user.session (pyrogram-формат),
        если он существует: форматы несовместимы.
    """
    from settings import API_ID, API_HASH, SESSIONS_DIR
    from telethon import TelegramClient

    session_path = SESSIONS_DIR / "user"

    print("\033[93m[user_client / Telethon]: Инициализация userbot-сессии\033[0m")
    print(f"  Файл сессии: {session_path}.session")

    async with TelegramClient(str(session_path), API_ID, API_HASH) as client:
        me = await client.get_me()
        print(f"\033[92m✓ Userbot авторизован: @{me.username or '—'} (id={me.id})\033[0m")

    print("\033[92m✓ Сессия создана. aiogram-бот использует BOT_TOKEN — bot.session не нужен.\033[0m")


# ---------------------------------------------------------------------------
# Точка входа
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if "--telethon" in sys.argv:
        asyncio.run(create_telethon_sessions())
    else:
        from clients import user_client  # noqa: E402

        user_client.run(create_pyrogram_sessions())
