import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')

LOGS_DIR = os.path.join(BASE_DIR, 'logs')
LOG_FORMAT = ('%(asctime)s : %(levelname)s : %(module)s : '
              '%(funcName)s : %(message)s')

DEVELOP_MODE = os.getenv('develop_mode')
