from datetime import datetime, timedelta

from common.links import get_message_link
from models import Category, MessageHistory, Source


def get_history_messages(
    category_id: int | None, period_hours: int
) -> list[tuple[str, str]]:
    """Получить сообщения истории за период.

    :param category_id: ID категории. Если None, то все категории.
    :param period_hours: Период в часах.
    :return: Список сообщений и ссылок на них.
    """
    since = datetime.now() - timedelta(hours=period_hours)

    mh: type[MessageHistory] = MessageHistory.alias()
    query = (
        mh.select(mh.data, mh.category_id, mh.category_message_id)
        .join(Source)
        .switch(mh)
        .join(Category)
        .where(mh.created_at >= since)
    )
    if category_id is not None:
        query = query.where(mh.category_id == category_id)

    items: list[tuple[str, str]] = []
    for row in query:
        data = row.data.get("last_message_without_error") or row.data.get(
            "first_message"
        )
        message_data = data.get("category") if data else {}
        text = message_data.get("text") or message_data.get("caption") or ""
        link = get_message_link(row.category_id, row.category_message_id)
        items.append((text, link))

    return items
