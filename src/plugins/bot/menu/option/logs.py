import logging
import os

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from config import LOGS_DIR
from plugins.bot.utils import custom_filters


@Client.on_callback_query(
    filters.regex(r'^/o/:get_logs/$') & custom_filters.admin_only,
)
async def get_logs(_, callback_query: CallbackQuery):
    await callback_query.answer('Загрузка...')
    info_message = ''
    for filename in os.listdir(LOGS_DIR):
        file_path = LOGS_DIR / filename
        if os.stat(file_path).st_size:
            await callback_query.message.reply_document(file_path)
        else:
            info_message += f'Файл **{filename}** пуст\n'
    if info_message:
        await callback_query.message.reply(info_message)
