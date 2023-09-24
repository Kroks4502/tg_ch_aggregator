from filter_types import FilterType
from models import Filter
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/f/\d+/")
async def detail_filter(menu: Menu):
    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    if menu.is_admin_user():
        if filter_obj.type not in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            menu.add_button.edit()
        menu.add_button.delete()

    return await menu.get_text(filter_obj=filter_obj)
