from clients import user
from plugins.bot import router
from plugins.bot.handlers.option.admin.common.utils import get_user_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/u/\d+/")
async def user_detail(menu: Menu):
    user_id = menu.path.get_value("u")

    if user_id != user.me.id:
        menu.add_button.delete()

    return await get_user_menu_text(user_id=user_id)
