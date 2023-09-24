from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

ASK_TEXT_TPL = (
    f"ОК. Ты добавляешь {{}} очистки текста{{}}.\n\n**Введи паттерн** или {CANCEL}"
)
SUC_TEXT_TPL = "✅ {} очистки текста `{}` добавлен {}"


@router.wait_input(send_to_admins=True)
async def add_cleanup_regex_waiting_input(
    message: Message,
    menu: Menu,
):
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj:
        source_obj.cleanup_list.append(pattern)
        source_obj.save()

        src_link = await get_channel_formatted_link(source_obj.id)
        return SUC_TEXT_TPL.format("Паттерн", pattern, f"для источника {src_link}")

    global_settings_obj = GlobalSettings.get(key="cleanup_list")
    global_settings_obj.value.append(pattern)
    global_settings_obj.save()

    return SUC_TEXT_TPL.format("Общий паттерн", pattern, "")


@router.page(
    path=r"/cl/:add/",
    reply=True,
    add_wait_for_input=add_cleanup_regex_waiting_input,
)
async def add_cleanup_regex(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.id)
        return ASK_TEXT_TPL.format("паттерн", f" для источника {src_link}")

    return ASK_TEXT_TPL.format("общий паттерн", "")
