from models import Category
from plugins import bot
from plugins.bot import router
from plugins.bot.utils.links import get_user_formatted_link


@router.page(path=r"/r/:add/")
async def add_alert_rule(menu: "bot.Menu"):
    menu.add_row_button("regex", "regex")
    menu.add_row_button("counter", "counter")

    category_id = menu.path.get_value("c")
    return await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"**Новое {'' if category_id else 'общее '}правило уведомления "
            f"{await get_user_formatted_link(menu.user.id)}**\n\n"
            "Выбери тип правила"
        ),
    )
