from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/o/")
async def options(menu: Menu):
    menu.add_row_button("Администраторы", "u")
    menu.add_row_button("💾 Логи", "logs")

    return "**Параметры**"
