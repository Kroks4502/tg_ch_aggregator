from models import Filter, Source
from plugins.bot import router
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/ft/\d+/f/", pagination=True, back_step=2)
async def list_filters(menu: Menu):
    filter_type_id = menu.path.get_value("ft")
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if menu.is_admin_user():
        menu.add_button.add()

    if source_obj:
        query = Filter.select().where(
            (Filter.source == source_id) & (Filter.type == filter_type_id)
        )
    else:
        query = Filter.select().where(
            Filter.source.is_null(True) & (Filter.type == filter_type_id)
        )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.pattern, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return await menu.get_text(source_obj=source_obj, filter_type_id=filter_type_id)
