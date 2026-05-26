import logging

from aiogram.exceptions import TelegramAPIError

from clients import aiogram_bot, user_client
from models import User

logger = logging.getLogger(__name__)


async def update_users_info_job():
    """Обновить информацию о пользователях бота."""
    logger.debug("Starting job...")
    for db_user in User.select().where(User.id != user_client.me.id):
        logger.debug(f"Updating info about user {db_user.id}...")
        try:
            tg_chat = await aiogram_bot.get_chat(db_user.id)
            if tg_chat.username and db_user.username != tg_chat.username:
                db_user.username = tg_chat.username
                db_user.save()
                logger.info(f"Username for user {db_user.id} updated")
        except TelegramAPIError as e:
            logger.error(
                f"При обновлении информации о пользователях произошла ошибка: {e}",
                exc_info=True,
            )
    logger.debug("Job completed")
