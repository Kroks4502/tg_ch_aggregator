import logging

from pyrogram.errors import RPCError

from clients import bot_client, user_client
from models import User


async def update_users_info_job():
    """Обновить информацию о пользователях бота."""
    for db_user in User.select().where(User.id != user_client.me.id):
        try:
            tg_user = await bot_client.get_users(db_user.id)
            if tg_user.username and db_user.username != tg_user.username:
                db_user.username = tg_user.username
                db_user.save()
        except RPCError as e:
            logging.error(
                f"При обновлении информации о пользователях произошла ошибка: {e}",
                exc_info=True,
            )
