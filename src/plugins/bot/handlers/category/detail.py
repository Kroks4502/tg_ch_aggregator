from plugins.bot import router
from plugins.bot.handlers.category.common.utils import get_category_menu_text
from plugins.bot.menu import Menu

CATEGORY_CALLBACK_DATA = "/c/{category_id}/"


@router.page(path=CATEGORY_CALLBACK_DATA.format(category_id=r"-\d+"))
async def detail_category(menu: Menu):
    category_id = menu.path.get_value("c")
    if menu.is_admin_user():
        menu.add_button.row_edit_delete()

    menu.add_button.sources(category_id=category_id)
    menu.add_button.alert_rules(
        user_id=menu.user.id,
        category_id=category_id,
    )
    menu.add_button.messages_histories()
    menu.add_button.filters_histories()
    menu.add_button.statistics()

    return await get_category_menu_text(category_id=category_id)
