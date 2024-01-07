from clients import user_client
from models import User
from plugins.bot import router
from plugins.bot.constants import symbols
from plugins.bot.handlers.option.user.common.constants import PLURAL_USER_TITLE
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text
from utils.menu import ButtonData


@router.page(path=r"/u/", pagination=True)
async def list_users(menu: Menu):
    query = User.select(
        User.id,
        User.username,
        User.is_admin,
    ).order_by(
        User.is_admin.desc(),
        User.last_interaction_at.desc(),
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(_get_title_for_user(i), i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return get_menu_text(title=PLURAL_USER_TITLE)


def _get_title_for_user(user: User):
    symbol = ""

    if user_client.me.id == user.id:
        symbol = f"{symbols.USER_BOT} "
    elif user.is_admin:
        symbol = f"{symbols.ADMIN} "

    return f"{symbol} {user.username}"
