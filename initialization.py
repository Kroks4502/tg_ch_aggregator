import logging
import os
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from pyrogram import Client

from models import db, Category, Source, Filter, Admin

db.create_tables(
    [
        Category, Source, Filter, Admin
    ]
)

LOGS_PATH = 'logs'
os.makedirs(LOGS_PATH, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s : %(levelname)s : %(module)s : '
           '%(funcName)s : %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = RotatingFileHandler(
    os.path.join(LOGS_PATH, 'main.log'), maxBytes=50000000, backupCount=5)

logger.addHandler(handler)
logger.addHandler(logging.StreamHandler())
load_dotenv()

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')
AGGREGATOR_CHANNEL = int(os.getenv('aggregator_channel'))

DEVELOP_MODE = os.getenv('develop_mode')

if DEVELOP_MODE:
    peewee_logger = logging.getLogger('peewee')
    peewee_logger.setLevel(logging.DEBUG)

user_plugins = dict(
    root='plugins.user',
    exclude=['news_forwarding', ] if DEVELOP_MODE else []
)
user = Client(
    'user', API_ID, API_HASH,
    plugins=user_plugins
)

bot_plugins = dict(
    root='plugins.bot',
    exclude=['news_forwarding', ] if DEVELOP_MODE else []
)
bot = Client(
    'bot', API_ID, API_HASH, bot_token=BOT_TOKEN,
    plugins=bot_plugins
)
