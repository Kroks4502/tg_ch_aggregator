import datetime as dt
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR.parent / "sessions"

LOGS_DIR = BASE_DIR.parent / "logs"
LOG_FORMAT = "%(asctime)s : %(name)s : %(levelname)s : %(message)s"

load_dotenv(BASE_DIR.parent / ".env")

API_ID = os.getenv("api_id")
API_HASH = os.getenv("api_hash")
BOT_TOKEN = os.getenv("bot_token")
DEVELOP_MODE = os.getenv("develop_mode")

TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_TEXT_LENGTH = 4096

USER_BOT_NAME = "🤖 UserBot"

APP_START_DATETIME = dt.datetime.now()

POSTGRESQL_DATABASE = os.getenv("postgresql_database")
POSTGRESQL_USER = os.getenv("postgresql_user")
POSTGRESQL_PASSWORD = os.getenv("postgresql_password")
POSTGRESQL_HOST = os.getenv("postgresql_host")
POSTGRESQL_PORT = os.getenv("postgresql_port")


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
