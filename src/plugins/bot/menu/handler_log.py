import logging

from pyrogram import Client
from pyrogram.types import CallbackQuery


@Client.on_callback_query(group=-999)
def log(_, callback_query: CallbackQuery):
    logging.debug(callback_query.data)
