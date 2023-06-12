import logging

from pyrogram.errors import RPCError

from clients import bot
from models import Admin


async def send_error_to_admins(
    text: str,
):
    """Отправка сообщений от бота всем администраторам."""
    for admin_tg_id in Admin.get_cache_admins_tg_ids():
        try:
            await bot.send_message(
                admin_tg_id,
                text,
                disable_web_page_preview=True,
            )
        except RPCError as e:
            logging.error(e, exc_info=True)
