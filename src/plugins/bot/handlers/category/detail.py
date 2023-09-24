from models import Category
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/c/-\d+/")
async def detail_category(menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj = Category.get(category_id) if category_id else None
    if category_obj and menu.is_admin_user():
        menu.add_button.row_edit_delete()

    menu.add_button.sources(category_id=category_id)
    menu.add_button.alert_rules(
        user_id=menu.user.id,
        category_id=category_id,
    )
    menu.add_button.messages_histories()
    menu.add_button.filters_histories()
    menu.add_button.statistics()

    return await menu.get_text(
        category_obj=category_obj,
    )
