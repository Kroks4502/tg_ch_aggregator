from alerts.common import get_alert_rule_title
from models import AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    PLURAL_ALERT_RULE_TITLE,
    PLURAL_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text
from plugins.bot.menu import Menu
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

    return await get_alert_rule_menu_text(
        title=PLURAL_ALERT_RULE_TITLE,
        title_common=PLURAL_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=category_id,
    )
