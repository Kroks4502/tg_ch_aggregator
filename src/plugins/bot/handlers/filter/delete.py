from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot import router
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

SUC_TEXT_TPL = "✅ {} типа **{}** c паттерном `{}` удален"


@router.page(path=r"/f/\d+/:delete/")
async def confirmation_delete_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    menu.add_button.confirmation_delete()

    return await menu.get_text(
        filter_obj=filter_obj,
        last_text=CONF_DEL_TEXT_TPL.format("фильтр"),
    )


@router.page(path=r"/f/\d+/:delete/:y/", back_step=3, send_to_admins=True)
async def delete_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    filter_obj.delete_instance()

    if filter_obj.source:
        src_link = await get_channel_formatted_link(filter_obj.source.id)
        title = f"Фильтр источника **{src_link}**"
    else:
        title = "Общий фильтр"
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    return SUC_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)
