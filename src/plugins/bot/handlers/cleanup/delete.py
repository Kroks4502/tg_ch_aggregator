from models import GlobalSettings, Source
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

SUC_TEXT_TPL = "✅ {} очистки текста `{}` удален {}"


@router.page(path=r"/cl/\d+/:delete/")
async def confirmation_delete_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj:
        pattern = source_obj.cleanup_list[cleanup_id]
    else:
        cleanup_list = GlobalSettings.get(key="cleanup_list").value
        pattern = cleanup_list[cleanup_id]

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        source_obj=source_obj,
        cleanup_pattern=pattern,
        last_text=CONF_DEL_TEXT_TPL.format("паттерн очистки текста"),
    )


@router.page(path=r"/cl/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_cleanup_regex(menu: Menu):
    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        pattern = source_obj.cleanup_list.pop(cleanup_id)
        source_obj.save()
        src_link = await get_channel_formatted_link(source_obj.id)
        return SUC_TEXT_TPL.format("Паттерн", pattern, f"из источника **{src_link}**")

    global_settings_obj = GlobalSettings.get(key="cleanup_list")
    pattern = global_settings_obj.value.pop(cleanup_id)
    global_settings_obj.save()
    return SUC_TEXT_TPL.format("Общий паттерн", pattern, "")
