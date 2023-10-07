from clients import user_client
from models import User
from plugins.bot import router
from plugins.bot.constants.settings import FORMAT_TIMESTAMP
from plugins.bot.handlers.option.user.common.constants import (
    PARAM_ADDED_AT_TEXT,
    PARAM_LAST_INTERACTION_AT_TEXT,
    PARAM_USER_ADMIN_TEXT,
    USER_DETAIL_TITLE,
)
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_user_formatted_link


@router.page(path=r"/u/\d+/")
async def user_detail(menu: Menu):
    user_id = menu.path.get_value("u")
    user_obj = User.get(user_id)

    if user_id != user_client.me.id:
        if user_obj.is_admin:
            menu.add_row_button("Разжаловать", "demote")
        else:
            menu.add_row_button("Повысить", "promote")

    user_link = await get_user_formatted_link(user_id)
    return get_menu_text(
        title=USER_DETAIL_TITLE.format(user_link),
        params=(
            (PARAM_USER_ADMIN_TEXT, user_obj.is_admin),
            (PARAM_ADDED_AT_TEXT, user_obj.added_at.strftime(FORMAT_TIMESTAMP)),
            (
                PARAM_LAST_INTERACTION_AT_TEXT,
                user_obj.last_interaction_at.strftime(FORMAT_TIMESTAMP),
            ),
        ),
    )
