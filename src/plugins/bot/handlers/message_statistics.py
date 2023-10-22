from datetime import datetime, timedelta

from peewee import CTE, Column, Expression, fn

from models import MessageHistory
from plugins.bot import menu_params as g_params
from plugins.bot import router
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text

STATISTIC_TMPL = """сообщений —  | день | нед. | месяц
- отправлено |{fdw_1d:5} |{fdw_7d:5} |{fdw_30d:6}
- отредакт.  |{edited_1d:5} |{edited_7d:5} |{edited_30d:6}
- отфильтр.  |{filtered_1d:5} |{filtered_7d:5} |{filtered_30d:6}
- удалено    |{deleted_1d:5} |{deleted_7d:5} |{deleted_30d:6}
- с ошибками |{errors_1d:5} |{errors_7d:5} |{errors_30d:6}"""

STATISTIC_TITLE = "Статистика сообщений"
COMMON_STATISTIC_TITLE = f"Общая {STATISTIC_TITLE.lower()}"


@router.page(path=r"/stat/")
async def message_history_statistics(menu: Menu):
    source_id = menu.path.get_value("s")
    category_id = menu.path.get_value("c")

    params = None
    statistic_where = None
    if source_id:
        params = (await g_params.source(source_id),)
        statistic_where = MessageHistory.source == source_id
    elif category_id:
        params = (await g_params.category(category_id),)
        statistic_where = MessageHistory.category == category_id

    return get_menu_text(
        title=STATISTIC_TITLE if source_id or category_id else COMMON_STATISTIC_TITLE,
        params=params,
        content=get_statistic_text(where=statistic_where),
    )


def get_statistic_text(where: Expression = None):
    where = where or True

    current_timestamp = datetime.now()
    interval_1d = current_timestamp - timedelta(days=1)
    interval_7d = current_timestamp - timedelta(days=7)
    interval_30d = current_timestamp - timedelta(days=30)

    counts_cte = (
        MessageHistory.select(
            MessageHistory.created_at,
            MessageHistory.edited_at,
            MessageHistory.filter_id,
            MessageHistory.deleted_at,
            MessageHistory.data.path("last_message_with_error").alias("error"),
        )
        .where(
            (MessageHistory.created_at >= interval_30d)
            & (MessageHistory.repeat_history_id.is_null(True))
            & where
        )
        .cte("Counts")
    )
    created_at = counts_cte.c.created_at
    edited_at = counts_cte.c.edited_at
    deleted_at = counts_cte.c.deleted_at
    filter_id = counts_cte.c.filter_id
    error = counts_cte.c.error

    query = (
        MessageHistory.select(
            fn.COUNT(created_at).alias("fdw_30d"),
            get_sub_query(counts_cte, created_at, interval_7d, "fdw_7d"),
            get_sub_query(counts_cte, created_at, interval_1d, "fdw_1d"),
            fn.COUNT(edited_at).alias("edited_30d"),
            get_sub_query(counts_cte, edited_at, interval_7d, "edited_7d"),
            get_sub_query(counts_cte, edited_at, interval_1d, "edited_1d"),
            fn.COUNT(filter_id).alias("filtered_30d"),
            get_sub_query(counts_cte, filter_id, interval_7d, "filtered_7d"),
            get_sub_query(counts_cte, filter_id, interval_1d, "filtered_1d"),
            fn.COUNT(counts_cte.c.deleted_at).alias("deleted_30d"),
            get_sub_query(counts_cte, deleted_at, interval_7d, "deleted_7d"),
            get_sub_query(counts_cte, deleted_at, interval_1d, "deleted_1d"),
            fn.COUNT(counts_cte.c.error).alias("errors_30d"),
            get_sub_query(counts_cte, error, interval_7d, "errors_7d"),
            get_sub_query(counts_cte, error, interval_1d, "errors_1d"),
        )
        .from_(counts_cte)
        .with_cte(counts_cte)
    )

    return f"`{STATISTIC_TMPL.format(**next(iter(query.dicts())))}`"


def get_sub_query(counts_cte: CTE, count_col: Column, interval: datetime, alias: str):
    return (
        counts_cte.select(fn.COUNT(count_col))
        .where(counts_cte.c.created_at >= interval)
        .alias(alias)
    )
