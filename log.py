import logging
import os
from logging.handlers import RotatingFileHandler

from settings import DEVELOP_MODE

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

if DEVELOP_MODE:
    peewee_logger = logging.getLogger('peewee')
    peewee_logger.setLevel(logging.DEBUG)
