import logging

from peewee import DoesNotExist

from clients import user_client
from models import User
from settings import USER_BOT_NAME

logger = logging.getLogger(__name__)


def set_user_bot_as_admin_job():
    logger.debug("Starting job...")
    try:
        user_obj = User.get(id=user_client.me.id)
        if not user_obj.is_admin:
            user_obj.is_admin = True
            user_obj.save()
            logger.info(f"UserBot {user_client.me.id} set as admin")
        else:
            logger.info(f"UserBot {user_client.me.id} is already admin")
    except DoesNotExist:
        User.create(id=user_client.me.id, username=USER_BOT_NAME, is_admin=True)
        logger.info(f"UserBot {user_client.me.id} created and set as admin")
    logger.debug("Job completed")
