from models import AlertHistory, AlertRule
from plugins.bot import router
from plugins.bot.constants.settings import FORMAT_TIMESTAMP
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_LIST_PATH,
    SINGULAR_ALERT_RULE_TITLE,
    SINGULAR_COMMON_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.alert_rules.common.utils import get_alert_rule_menu_text
from plugins.bot.menu import Menu


@router.page(
    path=ALERT_LIST_PATH.format(
        rule_id=r"\d+",
    ),
    pagination=True,
)
async def list_alerts(menu: Menu):
    rule_id = menu.path.get_value("r")
    rule_obj: AlertRule = AlertRule.get(rule_id)

    query = (
        AlertHistory.select()
        .where(AlertHistory.alert_rule_id == rule_id)
        .order_by(AlertHistory.fired_at.desc())
    )

    pagination = menu.set_pagination(total_items=query.count(), size=5)
    for i in query.paginate(pagination.page, pagination.size):
        menu.add_row_button(
            text=i.fired_at.strftime(FORMAT_TIMESTAMP),
            path=str(i.id),
        )

    return await get_alert_rule_menu_text(
        title=SINGULAR_ALERT_RULE_TITLE,
        title_common=SINGULAR_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=rule_obj.category_id,
        rule_type=rule_obj.type,
        **rule_obj.config,
        question="Сработавшие оповещения",
    )
