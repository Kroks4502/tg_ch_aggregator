from models import Category
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.page(path=r"/c/-\d+/:delete/")
async def confirmation_delete_category(menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        category_obj=category_obj,
        last_text=CONF_DEL_TEXT_TPL.format("категорию"),
    )


@router.page(path=r"/c/-\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_category(menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    category_obj.delete_instance()

    cat_link = await get_channel_formatted_link(category_obj.id)

    return f"✅ Категория **{cat_link}** удалена"
