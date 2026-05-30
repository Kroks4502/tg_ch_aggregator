from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from telethon import TelegramClient

from plugins.user.utils.album_collector import AlbumCollector
from settings import API_HASH, API_ID, BOT_TOKEN, SESSIONS_DIR

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# Userbot (Telethon) — заменяет pyrogram user_client
telethon_user_client = TelegramClient(
    str(SESSIONS_DIR / "user"),
    api_id=API_ID,
    api_hash=API_HASH,
)

# Буфер медиа-групп для userbot'а — собирает сообщения альбома перед обработкой
album_collector = AlbumCollector()

# ID userbot'а — устанавливается в set_user_bot_as_admin_job после get_me()
userbot_me_id: int | None = None

# Aiogram-бот. parse_mode=HTML — тексты хендлеров писались под pyrogram-MD,
# конвертируются в HTML через plugins.bot.text_formatter.pyrogram_markdown_to_html
# в router._send_final_text и notifiers.
aiogram_bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dispatcher = Dispatcher(storage=MemoryStorage())
