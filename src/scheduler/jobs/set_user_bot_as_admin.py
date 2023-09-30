from peewee import DoesNotExist

from clients import user_client
from models import User
from settings import USER_BOT_NAME


def set_user_bot_as_admin_job():
    try:
        user_obj = User.get(id=user_client.me.id)
        if not user_obj.is_admin:
            user_obj.is_admin = True
            user_obj.save()
    except DoesNotExist:
        User.create(id=user_client.me.id, username=USER_BOT_NAME, is_admin=True)
