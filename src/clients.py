from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from pyrogram import Client

from settings import API_HASH, API_ID, BOT_TOKEN, IS_ONLY_BOT, SESSIONS_DIR

SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

user_client = Client(
    "user",
    API_ID,
    API_HASH,
    plugins=(
        dict(
            root="plugins.user",
        )
        if not IS_ONLY_BOT
        else {}
    ),
    workdir=SESSIONS_DIR,
)

# Pyrogram bot_client остаётся в составе процесса до PR-3 (cutover) —
# он нужен для совместимости с мёртвыми импортами в common/call_handlers.py
# и common/senders.py. После cutover'а его старт убирается из main.py,
# а сам клиент удаляется на этапе 2 вместе с pyrogram.
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

# Aiogram-бот для нового стека. parse_mode пока не задан: существующие тексты
# используют pyrogram-flavoured Markdown ("**bold**", "__italic__"), который
# не совместим со стандартным Telegram-Markdown / HTML aiogram'а. После cutover
# в отдельном PR тексты переезжают на HTML и DefaultBotProperties выставляется
# на ParseMode.HTML.
aiogram_bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(storage=MemoryStorage())
