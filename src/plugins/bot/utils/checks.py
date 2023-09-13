import re

from models import User


def is_admin(user_id: int) -> bool:
    return user_id in User.get_cache_admins_tg_ids()


def is_valid_pattern(pattern: str) -> bool:
    try:
        re.compile(pattern)
    except (re.error, RecursionError):
        return False
    return True
