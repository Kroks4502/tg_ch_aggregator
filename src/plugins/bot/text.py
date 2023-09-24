from filter_types import FILTER_TYPES_BY_ID
from models import AlertRule, Category, Filter, Source, User
from plugins.bot.utils.links import get_channel_formatted_link, get_user_formatted_link


async def get_breadcrumbs(  # noqa: C901
    category_obj: Category = None,
    source_obj: Source = None,
    filter_obj: Filter = None,
    filter_type_id: str = None,
    cleanup_pattern: str = None,
    user_obj: User = None,
    alert_rule_obj: AlertRule = None,
) -> str:
    if filter_obj:
        source_obj = filter_obj.source
        filter_type_id = filter_obj.type

    if source_obj:
        category_obj = source_obj.category

    if alert_rule_obj:
        category_obj = alert_rule_obj.category

    breadcrumbs = []

    if category_obj:
        link = await get_channel_formatted_link(category_obj.id)
        breadcrumbs.append(f"Категория: **{link}**")

    if source_obj:
        link = await get_channel_formatted_link(source_obj.id)
        breadcrumbs.append(f"Источник: **{link}**")

    if filter_type_id:
        if not source_obj:
            breadcrumbs.append("**Общие фильтры**")
        filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)
        breadcrumbs.append(f"Тип фильтра: **{filter_type_text}**")

    if filter_obj:
        breadcrumbs.append(f"Паттерн: `{filter_obj.pattern}`")

    if cleanup_pattern:
        if not source_obj:
            breadcrumbs.append("**Общая очистка текста**")
        breadcrumbs.append(f"Паттерн очистки текста: `{cleanup_pattern}`")

    if user_obj:
        link = await get_user_formatted_link(user_obj.id)
        breadcrumbs.append(f"Пользователь: **{link}**")

    if alert_rule_obj:
        link = await get_user_formatted_link(alert_rule_obj.user_id)
        if alert_rule_obj.category_id:
            breadcrumbs.append(f"**Правила уведомления {link}**")
        else:
            breadcrumbs.append(f"**Общие правила уведомлений {link}**")

    return "\n".join(breadcrumbs)
