import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from config import DB_FILEPATH
from plugins.bot.utils import custom_filters


@Client.on_callback_query(
    filters.regex(r'^/o/:get_db/') & custom_filters.admin_only,
)
async def get_db(_, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    await callback_query.answer('Загрузка...')
    await callback_query.message.reply_document(DB_FILEPATH)
