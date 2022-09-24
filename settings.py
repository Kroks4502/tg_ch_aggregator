import os

from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('api_id')
API_HASH = os.getenv('api_hash')
BOT_TOKEN = os.getenv('bot_token')
AGGREGATOR_CHANNEL = int(os.getenv('aggregator_channel'))

DEVELOP_MODE = os.getenv('develop_mode')
