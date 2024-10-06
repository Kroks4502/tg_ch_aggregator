from pyrogram.types import CallbackQuery

from clients import user_client
from models import Source
from plugins.bot import router
from plugins.bot.handlers.source.common.constants import (
    SUCCESS_ACTION_MODE_SWITCHING_TEXT,
)
from plugins.bot.handlers.source.common.utils import get_source_menu_success_text
from plugins.bot.menu import Menu


@router.page(path=r"/s/-\d+/:edit/:(on|off)_rewrite/", send_to_admins=True)
async def set_rewrite(menu: Menu, callback_query: CallbackQuery):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(
        id=source_id,
        is_deleted=False,
    )

    if callback_query.data.endswith("on_rewrite/"):
        source_obj.is_rewrite = True
        mode = "перепечатывания"
    else:
        source_obj.is_rewrite = True
        mode = "пересылки"
        chat = await user_client.get_chat(source_id)
        if chat.has_protected_content:
            mode += ", но канал запрещает пересылку сообщений! ⚠"
    source_obj.save()

    return await get_source_menu_success_text(
        source_id=source_id,
        action=SUCCESS_ACTION_MODE_SWITCHING_TEXT.format(mode),
    )
