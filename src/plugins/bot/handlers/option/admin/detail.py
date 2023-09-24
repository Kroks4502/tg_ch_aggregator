from clients import user
from models import User
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/a/\d+/")
async def detail_admin(menu: Menu):
    admin_id = menu.path.get_value("a")
    admin_obj: User = User.get(admin_id)

    if admin_obj.id != user.me.id:
        menu.add_button.delete()

    return await menu.get_text(user_obj=admin_obj)
