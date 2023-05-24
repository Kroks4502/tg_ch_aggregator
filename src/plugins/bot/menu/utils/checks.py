from models import Admin


def is_admin(user_id: int) -> bool:
    return (Admin
            .select()
            .where(Admin.tg_id == user_id)
            .exists())
