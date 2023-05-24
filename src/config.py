import datetime
import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from peewee import SqliteDatabase

BASE_DIR = Path(__file__).parent
DB_FILEPATH = BASE_DIR.parent / '.db'
SESSIONS_DIR = BASE_DIR.parent / 'sessions'

LOGS_DIR = BASE_DIR.parent / 'logs'
LOG_FORMAT = '%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(message)s'

load_dotenv(BASE_DIR.parent / '.env')
API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')
DEVELOP_MODE = os.getenv('develop_mode')

PATTERN_AGENT = re.compile(
    (r'\s*Д*АН*ОЕ\sСООБЩЕНИЕ[\w\s().,]+ИНОСТРАННОГО\s(АГЕНТА|)*[\s.]*\s*|\s*([\d +]+|)НАСТОЯЩИЙ МАТЕРИАЛ'
     r'[\w \t\x0B\f\r().,+]+[\r\n]*'),
    flags=re.IGNORECASE
)
PATTERN_WITHOUT_SMILE = re.compile(
    r'[^а-яА-ЯЁёa-zA-z0-9 |-]+',
    flags=re.IGNORECASE
)

DATABASE = SqliteDatabase(DB_FILEPATH, pragmas={'foreign_keys': 1})

# Период в течение которого при редактировании сообщения в источнике, происходит пересылка в категорию
MESSAGES_EDIT_LIMIT_TD = datetime.timedelta(minutes=60)


def configure_logging():
    """Конфигурирование логирования."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOGS_DIR / 'app.log',
        maxBytes=10 ** 6,
        backupCount=5,
        encoding='UTF-8'
    )
    logging.basicConfig(
        format=LOG_FORMAT,
        level=logging.WARNING,
        handlers=(rotating_handler, logging.StreamHandler())
    )

    if DEVELOP_MODE:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('peewee').setLevel(logging.DEBUG)
        logging.getLogger('pyrogram').setLevel(logging.INFO)
