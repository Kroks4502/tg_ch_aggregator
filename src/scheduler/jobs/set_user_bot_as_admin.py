import logging

from peewee import DoesNotExist

from clients import telethon_user_client
from models import User
from settings import USER_BOT_NAME

logger = logging.getLogger(__name__)


async def set_user_bot_as_admin_job():
    """Установить userbot как администратора в таблице User."""
    logger.debug("Starting job...")
    me = await telethon_user_client.get_me()
    user_id = me.id

    try:
        user_obj = User.get(id=user_id)
        if not user_obj.is_admin:
            user_obj.is_admin = True
            user_obj.save()
            logger.info("UserBot %s set as admin", user_id)
        else:
            logger.info("UserBot %s is already admin", user_id)
    except DoesNotExist:
        User.create(id=user_id, username=USER_BOT_NAME, is_admin=True)
        logger.info("UserBot %s created and set as admin", user_id)

    # Сохраняем ID в clients для использования в bot handlers
    import clients

    clients.userbot_me_id = user_id

    logger.debug("Job completed")
