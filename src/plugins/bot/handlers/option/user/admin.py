from models import User
from plugins.bot import router
from plugins.bot.handlers.option.user.common.constants import (
    ACTION_DEMOTE_USER,
    ACTION_PROMOTE_USER,
)
from plugins.bot.handlers.option.user.common.utils import get_user_menu_success_text
from plugins.bot.menu import Menu


@router.page(path=r"/u/\d+/(promote|demote)/", send_to_admins=True)
async def promote_demote_user(menu: Menu):
    user_id = menu.path.get_value("u")
    user_obj = User.get(user_id)

    if menu.path.raw_path.endswith("promote/"):
        user_obj.is_admin = True
        action = ACTION_PROMOTE_USER
    else:
        user_obj.is_admin = False
        action = ACTION_DEMOTE_USER
    user_obj.save()

    return await get_user_menu_success_text(
        user_id=user_id,
        action=action,
    )
