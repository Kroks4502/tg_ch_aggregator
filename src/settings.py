import datetime as dt
import logging
import os
import platform
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

from plugins.user.types import Operation

APP_VERSION = f"Migrate to telethon 0.0.0"
DEVICE_MODEL = f"{platform.python_implementation()} {platform.python_version()}"
SYSTEM_VERSION = f"{platform.system()} {platform.release()}"

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR.parent / "sessions_telethon"
DUMP_MESSAGES_DIR = BASE_DIR.parent / "tests" / "dump_messages"
DUMP_MESSAGES_DIRS_BY_OPERATION = {
    Operation.NEW: DUMP_MESSAGES_DIR / "new_message",
    Operation.NEW_GROUP: DUMP_MESSAGES_DIR / "new_group_messages",
    Operation.EDIT: DUMP_MESSAGES_DIR / "edited_messages",
    Operation.DELETE: DUMP_MESSAGES_DIR / "deleted_messages",
}

LOGS_DIR = BASE_DIR.parent / "logs"
LOG_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"

load_dotenv(BASE_DIR.parent / ".env")

API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
DEVELOP_MODE = os.getenv("develop_mode")
DUMP_MESSAGE_MODE = os.getenv("dump_message_mode", False)

TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_TEXT_LENGTH = 4096

USER_BOT_NAME = "UserBot"

APP_START_DATETIME = dt.datetime.now()

POSTGRESQL_DATABASE = os.getenv("postgresql_database")
POSTGRESQL_USER = os.getenv("postgresql_user")
POSTGRESQL_PASSWORD = os.getenv("postgresql_password")
POSTGRESQL_HOST = os.getenv("postgresql_host")
POSTGRESQL_PORT = os.getenv("postgresql_port")


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
        logging.getLogger("telethon.client.updates").setLevel(logging.DEBUG)
        logging.getLogger("telethon.network").setLevel(logging.DEBUG)
        # logging.getLogger("pyrogram").setLevel(logging.INFO)
        logging.getLogger("apscheduler").setLevel(logging.INFO)
