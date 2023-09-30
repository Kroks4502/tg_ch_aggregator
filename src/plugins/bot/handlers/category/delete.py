from models import Category
from plugins.bot import router
from plugins.bot.handlers.category.common.constants import QUESTION_CONF_DEL
from plugins.bot.handlers.category.common.utils import (
    get_category_menu_success_text,
    get_category_menu_text,
)
from plugins.bot.menu import Menu


@router.page(path=r"/c/-\d+/:delete/")
async def category_deletion_confirmation(menu: Menu):
    category_id = menu.path.get_value("c")

    menu.add_button.confirmation_delete()

    return await get_category_menu_text(
        category_id=category_id,
        question=QUESTION_CONF_DEL,
    )


@router.page(path=r"/c/-\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_category(menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    category_obj.delete_instance()

    return await get_category_menu_success_text(
        category_id=category_obj.id,
        action="удалена",
    )
