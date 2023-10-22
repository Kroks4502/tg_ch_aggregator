from datetime import datetime, timedelta

from peewee import fn

from filter_types import FILTER_TYPES_BY_ID
from models import Filter, MessageHistory
from plugins.bot import menu_params as g_params
from plugins.bot import router
from plugins.bot.handlers.statistics.common.constants import (
    STATISTIC_FILTER_ANTI_TOP_10,
    STATISTIC_FILTER_COMMON_TITLE,
    STATISTIC_FILTER_DATA_NOT_FOUND,
    STATISTIC_FILTER_LINE,
    STATISTIC_FILTER_TITLE,
    STATISTIC_FILTER_TOP_10,
)
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text

INTERVAL_BUTTONS_DATA = {
    1: ("1d", "../1"),
    7: ("7d", "../7"),
    14: ("14d", "../14"),
    30: ("1m", "../30"),
    60: ("2m", "../60"),
    90: ("3m", "../90"),
    180: ("6m", "../180"),
    365: ("1y", "../365"),
}


@router.page(path=r"/stat/f/d/\d+/", back_step=3)
async def filter_history_statistics(menu: Menu):
    source_id = menu.path.get_value("s")
    days = menu.path.get_value("d")

    menu.add_row_many_buttons(
        *(bt_data for day, bt_data in INTERVAL_BUTTONS_DATA.items() if day != days)
    )

    return get_menu_text(
        title=(
            STATISTIC_FILTER_TITLE if source_id else STATISTIC_FILTER_COMMON_TITLE
        ).format(days),
        params=(await g_params.source(source_id),) if source_id else None,
        content=get_content(days, source_id),
    )


def get_content(days: int, source_id: int | None):
    content_items = []
    interval = datetime.now() - timedelta(days=days)
    if top_10 := get_top_10(interval, source_id=source_id):
        content_items.append(STATISTIC_FILTER_TOP_10.format(top_10))

    if anti_top := get_anti_top_10(interval, source_id=source_id):
        content_items.append(STATISTIC_FILTER_ANTI_TOP_10.format(anti_top))

    if content_items:
        return "\n\n".join(content_items)

    return STATISTIC_FILTER_DATA_NOT_FOUND


def get_top_10(interval: datetime, source_id: int | None):
    cond = (
        (MessageHistory.filter_id == Filter.id)
        & (MessageHistory.created_at >= interval)
        & (MessageHistory.repeat_history_id.is_null(True))
    )
    if source_id:
        cond &= MessageHistory.source == source_id

    count = fn.COUNT(MessageHistory.id).alias("c")
    query = (
        Filter.select(
            count,
            Filter.id,
            Filter.pattern,
            Filter.type,
        )
        .join(MessageHistory, on=cond)
        .group_by(Filter.id)
        .order_by(count.desc())
        .limit(10)
    )

    lines = []
    for top_n, filter_h in enumerate(query, 1):
        lines.append(
            STATISTIC_FILTER_LINE.format(
                amount=filter_h.c,
                id=filter_h.id,
                type=FILTER_TYPES_BY_ID.get(filter_h.type),
                pattern=filter_h.pattern,
            ),
        )

    return "\n".join(lines)


def get_anti_top_10(interval: datetime, source_id: int | None):
    cond = ~fn.EXISTS(
        MessageHistory.select(None).where(
            (MessageHistory.filter_id == Filter.id)
            & (MessageHistory.created_at >= interval)
            & (MessageHistory.repeat_history_id.is_null(True))
        )
    )
    if source_id:
        cond = (Filter.source_id == source_id) & cond

    query = (
        Filter.select(
            Filter.id,
            Filter.pattern,
            Filter.type,
        )
        .where(cond)
        .limit(10)
    )

    lines = []
    for top_n, filter_h in enumerate(query, 1):
        lines.append(
            STATISTIC_FILTER_LINE.format(
                amount=0,
                id=filter_h.id,
                type=FILTER_TYPES_BY_ID.get(filter_h.type),
                pattern=filter_h.pattern,
            ),
        )

    return "\n".join(lines)
