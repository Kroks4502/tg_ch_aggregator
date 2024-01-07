import os

from pyrogram.types import CallbackQuery

from plugins.bot import router
from settings import LOGS_DIR


@router.page(path=r"/logs/", callback_answer_text="Загрузка...")
async def get_logs(callback_query: CallbackQuery):
    info_message = ""
    for filename in os.listdir(LOGS_DIR):
        file_path = LOGS_DIR / filename
        if os.stat(file_path).st_size:
            await callback_query.message.reply_document(file_path)
        else:
            info_message += f"Файл **{filename}** пуст\n"
    if info_message:
        await callback_query.message.reply(info_message)
