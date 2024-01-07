from plugins.bot.constants.text import SUCCESS_TEXT
from plugins.bot.handlers.option.user.common.constants import SINGULAR_USER_TITLE
from plugins.bot.utils.links import get_user_formatted_link


async def get_user_menu_success_text(
    user_id: int,
    action: str,
) -> str:
    user_link = await get_user_formatted_link(user_id)
    return SUCCESS_TEXT.format(
        text=f"{SINGULAR_USER_TITLE} **{user_link}** ({user_id}) {action}"
    )
