from pyrogram import Client
from pyrogram.types import CallbackQuery

from initialization import logger


@Client.on_callback_query(group=-999)
def log(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)
