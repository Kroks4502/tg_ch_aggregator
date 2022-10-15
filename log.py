import logging
import os
from logging.handlers import RotatingFileHandler

from settings import DEVELOP_MODE, LOG_FORMAT, LOGS_DIR

os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(level=logging.WARNING, format=LOG_FORMAT, encoding='utf-8')

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)
handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'app.log'),
                              maxBytes=50000000, backupCount=5, encoding='utf-8')
handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(handler)

peewee_logger = logging.getLogger('peewee')
peewee_logger.setLevel(logging.WARNING)
peewee_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'peewee.log'),
                                     maxBytes=50000000, backupCount=5, encoding='utf-8')
peewee_handler.setFormatter(logging.Formatter(LOG_FORMAT))
peewee_logger.addHandler(peewee_handler)

pyrogram_logger = logging.getLogger('pyrogram')
pyrogram_logger.setLevel(logging.WARNING)
pyrogram_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'pyrogram.log'),
                                       maxBytes=50000000, backupCount=5, encoding='utf-8')
pyrogram_handler.setFormatter(logging.Formatter(LOG_FORMAT))
pyrogram_logger.addHandler(pyrogram_handler)


if DEVELOP_MODE:
    peewee_logger.setLevel(logging.DEBUG)
    pyrogram_logger.setLevel(logging.INFO)
    logger.setLevel(logging.DEBUG)
