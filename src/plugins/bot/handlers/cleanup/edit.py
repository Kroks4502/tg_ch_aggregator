from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

ASK_TEXT_TPL = (
    "ОК. Ты изменяешь {} очистки текста `{}`{}.\n\n"
    f"**Введи новый паттерн** или {CANCEL}"
)
SUC_TEXT_TPL = "✅ {} очистки текста изменен с `{}` на `{}` {}"


@router.wait_input(send_to_admins=True)
async def edit_cleanup_regex_wait_input(
    message: Message,
    menu: Menu,
):
    pattern_new = str(message.text)
    validators.is_valid_pattern(pattern_new)

    cleanup_id = menu.path.get_value("cl")
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        cleanup_list = source_obj.cleanup_list
        pattern_old = cleanup_list[cleanup_id]
        cleanup_list[cleanup_id] = pattern_new
        source_obj.save()
        src_link = await get_channel_formatted_link(source_obj.id)

        return SUC_TEXT_TPL.format(
            "Паттерн",
            pattern_old,
            pattern_new,
            f"для источника **{src_link}**",
        )

    global_settings_obj = GlobalSettings.get(key="cleanup_list")
    cleanup_list = global_settings_obj.value
    pattern_old = cleanup_list[cleanup_id]
    cleanup_list[cleanup_id] = pattern_new
    global_settings_obj.save()

    return SUC_TEXT_TPL.format(
        "Общий паттерн",
        pattern_old,
        pattern_new,
        "",
    )


@router.page(
    path=r"/cl/\d+/:edit/",
    reply=True,
    add_wait_for_input=edit_cleanup_regex_wait_input,
)
async def edit_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        pattern = source_obj.cleanup_list[cleanup_id]
        src_link = await get_channel_formatted_link(source_obj.id)
        return ASK_TEXT_TPL.format("паттерн", pattern, f" для источника {src_link}")

    global_settings_obj = GlobalSettings.get(key="cleanup_list")
    pattern = global_settings_obj.value[cleanup_id]
    return ASK_TEXT_TPL.format("общий паттерн", pattern, "")
