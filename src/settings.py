import datetime as dt
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

from plugins.user.types import Operation

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR.parent / "sessions"
DUMP_MESSAGES_DIR = BASE_DIR.parent / "tests" / "dump_messages"
DUMP_MESSAGES_DIRS_BY_OPERATION = {
    Operation.NEW: DUMP_MESSAGES_DIR / "new_messages",
    Operation.EDIT: DUMP_MESSAGES_DIR / "edited_messages",
    Operation.DELETE: DUMP_MESSAGES_DIR / "deleted_messages",
}

LOGS_DIR = BASE_DIR.parent / "logs"
LOG_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"

load_dotenv(BASE_DIR.parent / ".env")

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEVELOP_MODE = os.getenv("DEVELOP_MODE")
DUMP_MESSAGE_MODE = os.getenv("DUMP_MESSAGE_MODE", False)

TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_TEXT_LENGTH = 4096

USER_BOT_NAME = "UserBot"

APP_START_DATETIME = dt.datetime.now()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

IS_ONLY_BOT = True if DEVELOP_MODE == "bot" else False

if DUMP_MESSAGE_MODE:
    for directory in DUMP_MESSAGES_DIRS_BY_OPERATION.values():
        directory.mkdir(parents=True, exist_ok=True)


def configure_logging():
    """Конфигурирование логирования."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOGS_DIR / "app.log",
        maxBytes=10**6,
        backupCount=5,
        encoding="UTF-8",
    )
    logging.basicConfig(
        format=LOG_FORMAT,
        level=logging.WARNING,
        handlers=(rotating_handler, logging.StreamHandler()),
    )

    if DEVELOP_MODE:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("peewee").setLevel(logging.DEBUG)
        logging.getLogger("pyrogram").setLevel(logging.INFO)
        logging.getLogger("apscheduler").setLevel(logging.INFO)
