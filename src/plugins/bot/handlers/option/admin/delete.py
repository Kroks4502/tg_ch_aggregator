from models import User
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_user_formatted_link


@router.page(path=r"/a/\d+/:delete/")
async def confirmation_delete_admin(menu: Menu):
    admin_id = menu.path.get_value("a")
    admin_obj: User = User.get(admin_id)

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        user_obj=admin_obj,
        last_text=CONF_DEL_TEXT_TPL.format("администратора"),
    )


@router.page(path=r"/a/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_admin(menu: Menu):
    admin_id = menu.path.get_value("a")
    admin_obj: User = User.get(admin_id)

    admin_obj.delete_instance()

    adm_link = await get_user_formatted_link(admin_obj.id)
    return f"✅ Администратор **{adm_link}** удален"
