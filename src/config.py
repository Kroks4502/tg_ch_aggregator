import datetime as dt
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from gevent.socket import wait_read, wait_write
from playhouse.postgres_ext import PostgresqlExtDatabase
from psycopg2 import extensions

from plugins.user.types import Operation

BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR.parent / 'sessions'
DUMP_MESSAGES_DIR = BASE_DIR.parent / 'tests' / 'dump_messages'
DUMP_MESSAGES_DIRS_BY_OPERATION = {
    Operation.NEW: DUMP_MESSAGES_DIR / 'new_messages',
    Operation.EDIT: DUMP_MESSAGES_DIR / 'edited_messages',
    Operation.DELETE: DUMP_MESSAGES_DIR / 'deleted_messages',
}

LOGS_DIR = BASE_DIR.parent / 'logs'
LOG_FORMAT = '%(asctime)s : %(levelname)s : %(message)s'

load_dotenv(BASE_DIR.parent / '.env')
API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')
DEVELOP_MODE = bool(os.getenv('develop_mode', False))
DUMP_MESSAGE_MODE = bool(os.getenv('dump_message_mode', False))

TELEGRAM_MAX_CAPTION_LENGTH = 1024
TELEGRAM_MAX_TEXT_LENGTH = 4096

APP_START_DATETIME = dt.datetime.now()


if DUMP_MESSAGE_MODE:
    for directory in DUMP_MESSAGES_DIRS_BY_OPERATION.values():
        directory.mkdir(parents=True, exist_ok=True)


def patch_psycopg2():
    extensions.set_wait_callback(_psycopg2_gevent_callback)


def _psycopg2_gevent_callback(conn, timeout=None):
    while True:
        state = conn.poll()
        if state == extensions.POLL_OK:
            break
        if state == extensions.POLL_READ:
            wait_read(conn.fileno(), timeout=timeout)
        elif state == extensions.POLL_WRITE:
            wait_write(conn.fileno(), timeout=timeout)
        else:
            raise ValueError('poll() returned unexpected result')


DATABASE = PostgresqlExtDatabase(
    os.getenv('postgresql_database'),
    user=os.getenv('postgresql_user'),
    password=os.getenv('postgresql_password'),
    host=os.getenv('postgresql_host'),
    port=os.getenv('postgresql_port'),
)


def configure_logging():
    """Конфигурирование логирования."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    rotating_handler = RotatingFileHandler(
        LOGS_DIR / 'app.log',
        maxBytes=10**6,
        backupCount=5,
        encoding='UTF-8',
    )
    logging.basicConfig(
        format=LOG_FORMAT,
        level=logging.WARNING,
        handlers=(rotating_handler, logging.StreamHandler()),
    )

    if DEVELOP_MODE:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('peewee').setLevel(logging.DEBUG)
        logging.getLogger('pyrogram').setLevel(logging.INFO)
