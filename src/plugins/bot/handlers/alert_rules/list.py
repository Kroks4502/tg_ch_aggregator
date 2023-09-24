from alerts.common import get_alert_rule_title
from models import AlertRule, Category
from plugins.bot import router
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_user_formatted_link
from utils.menu import ButtonData


@router.page(path=r"/r/", pagination=True)
async def list_alerts_rules(menu: Menu):
    category_id = menu.path.get_value("c")

    if menu.is_admin_user():
        menu.add_button.add()

    query = AlertRule.select().where(
        (AlertRule.user_id == menu.user.id) & (AlertRule.category_id == category_id)
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(
                title=get_alert_rule_title(alert_rule=i),
                path=i.id,
            )
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    return await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"**{'П' if category_id else 'Общие п'}равила уведомлений"
            f" {await get_user_formatted_link(menu.user.id)}**"
        ),
    )
