from models import Source
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.page(path=r"/s/-\d+/:delete/")
async def confirmation_delete_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        source_obj=source_obj,
        last_text=CONF_DEL_TEXT_TPL.format("источник"),
    )


@router.page(path=r"/s/-\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    source_obj.delete_instance()

    src_link = await get_channel_formatted_link(source_obj.id)
    return f"✅ Источник **{src_link}** удален"
