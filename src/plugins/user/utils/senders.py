import logging

from pyrogram.errors import RPCError

from clients import bot_client
from models import User


async def send_error_to_admins(
    text: str,
):
    """Отправка сообщений от бота всем администраторам."""
    admins = User.select(User.id).where(User.is_admin == True)
    for admin in admins:
        try:
            await bot_client.send_message(
                admin.id,
                text,
                disable_web_page_preview=True,
            )
        except RPCError as e:
            logging.error(e, exc_info=True)
