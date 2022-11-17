import datetime
import os
import re

from dotenv import load_dotenv
from peewee import SqliteDatabase

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FORMAT = ('%(asctime)s : %(levelname)s : %(module)s : '
              '%(funcName)s : %(message)s')

DEVELOP_MODE = os.getenv('develop_mode')
PATTERN_AGENT = re.compile(
    r'\s*Д*АН*ОЕ\sСООБЩЕНИЕ[\w\s().,]+ИНОСТРАННОГО\s(АГЕНТА|)*[\s.]*\s*',
    flags=re.IGNORECASE)
PATTERN_WITHOUT_SMILE = re.compile(
    r'[^а-яА-ЯЁёa-zA-z0-9 |-]+',
    flags=re.IGNORECASE)

DATABASE = SqliteDatabase('.db', pragmas={'foreign_keys': 1})
MESSAGES_EDIT_LIMIT_TD = datetime.timedelta(minutes=60)
