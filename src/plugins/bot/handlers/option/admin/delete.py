from models import User
from plugins.bot import router
from plugins.bot.handlers.option.admin.common.constants import QUESTION_CONF_DEL
from plugins.bot.handlers.option.admin.common.utils import (
    get_user_menu_success_text,
    get_user_menu_text,
)
from plugins.bot.menu import Menu


@router.page(path=r"/u/\d+/:delete/")
async def user_deletion_confirmation(menu: Menu):
    user_id = menu.path.get_value("u")

    menu.add_button.confirmation_delete()

    return await get_user_menu_text(
        user_id=user_id,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/u/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_user(menu: Menu):
    user_id = menu.path.get_value("u")
    user_obj: User = User.get(user_id)

    user_obj.delete_instance()

    return await get_user_menu_success_text(user_id=user_id, action="удален")
