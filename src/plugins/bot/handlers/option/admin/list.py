from models import User
from plugins.bot import router
from plugins.bot.menu import Menu
from utils.menu import ButtonData


@router.page(path=r"/a/", pagination=True)
async def list_admins(menu: Menu):
    menu.add_button.add()

    query = User.select(
        User.id,
        User.username,
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.username, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return "**Список администраторов:**"
