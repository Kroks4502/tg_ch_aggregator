from pyrogram.types import CallbackQuery

from clients import user
from models import Source
from plugins.bot import router
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

REWRITE_TEXT_TPL = "✅ Установлен режим {} сообщений для источника {}"


@router.page(path=r"/s/-\d+/:edit/:(on|off)_rewrite/", send_to_admins=True)
async def set_rewrite(menu: Menu, callback_query: CallbackQuery):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    src_link = await get_channel_formatted_link(source_obj.id)
    if callback_query.data.endswith("off_rewrite/"):
        source_obj.is_rewrite = False
        source_obj.save()
        text = REWRITE_TEXT_TPL.format("пересылки", src_link)
        chat = await user.get_chat(source_obj.id)
        if chat.has_protected_content:
            text += ", но канал запрещает пересылку сообщений! ⚠"
        return text

    source_obj.is_rewrite = True
    source_obj.save()

    return REWRITE_TEXT_TPL.format("перепечатывания", src_link)
