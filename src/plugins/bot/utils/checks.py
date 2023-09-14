import re

from models import User


def is_admin(user_id: int) -> bool:
    return User.select().where((User.id == user_id) & (User.is_admin == True)).exists()


def is_valid_pattern(pattern: str) -> bool:
    try:
        re.compile(pattern)
    except (re.error, RecursionError):
        return False
    return True
