from models import User
from plugins.bot import router
from plugins.bot.handlers.option.admin.common.constants import PLURAL_USER_TITLE
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text
from utils.menu import ButtonData


@router.page(path=r"/u/", pagination=True)
async def list_users(menu: Menu):
    menu.add_button.add()

    query = User.select(
        User.id,
        User.username,
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.username, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return get_menu_text(title=PLURAL_USER_TITLE)
