from models import Admin


def is_admin(user_id):
    return (Admin
            .select()
            .where(Admin.tg_id == user_id)
            .exists())
