from models import Admin


def is_admin(user_id: int) -> bool:
    return user_id in Admin.get_cache_admins_tg_ids()
