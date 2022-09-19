import logging
import os

from dotenv import load_dotenv
from pyrogram import Client

from models import db, Category, Source, Filter, Admin

db.create_tables(
    [
        Category, Source, Filter, Admin
    ]
)

logging.basicConfig(
    format='%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : '
           '%(message)s',
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

LOGS_PATH = 'logs'
os.makedirs(LOGS_PATH, exist_ok=True)

handler = logging.FileHandler(os.path.join(LOGS_PATH, 'log_file.log'),
                              encoding='utf8')
handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(message)s'
))
logger.addHandler(handler)

logger2 = logging.getLogger()
logger2.setLevel(logging.WARNING)
handler = logging.FileHandler(os.path.join(
    LOGS_PATH, 'log_file_all_warning.log'), encoding='utf8')
handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s : %(levelname)s : %(module)s : %(funcName)s : %(message)s'
))
logger2.addHandler(handler)

peewee_logger = logging.getLogger('peewee')
peewee_logger.setLevel(logging.DEBUG)

load_dotenv()

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')
AGGREGATOR_CHANNEL = int(os.getenv('aggregator_channel'))

DEVELOP_MODE = False

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

MONITORED_CHANNELS_ID = Source.get_all_ids()
