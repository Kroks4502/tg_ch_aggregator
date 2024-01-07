from peewee import SQL, fn

from alerts.configs import AlertCounterConfig, AlertCounterHistory
from common.call_handlers import call_callback_query_handler
from models import AlertHistory, AlertRule, MessageHistory
from plugins.bot.handlers.alert_rules.alert.detail import alert_detail
from plugins.bot.handlers.alert_rules.common.constants import ALERT_DETAIL_PATH


async def evaluation_counter_rule_job(rule_obj: AlertRule):
    """Задача оценки правила уведомления типа счётчик для планировщика."""
    config = AlertCounterConfig(**rule_obj.config)

    amount_messages = _get_amount_messages(
        category_id=rule_obj.category_id,
        count_interval=config.count_interval,
    )
    if amount_messages > config.threshold:
        alert_obj = AlertHistory.create(
            category_id=rule_obj.category_id,
            data=AlertCounterHistory(
                type=rule_obj.type,
                user_id=rule_obj.user_id,
                actual_amount_messages=amount_messages,
                **rule_obj.config,
            ),
            alert_rule_id=rule_obj.id,
        )

        await call_callback_query_handler(
            func=alert_detail,
            user_id=rule_obj.user_id,
            path=(
                ALERT_DETAIL_PATH.format(
                    alert_id=alert_obj.id,
                )
                + "?new"
            ),
        )


def _get_amount_messages(category_id: int | None, count_interval: int) -> int:
    """Получить количество сообщений в категории за последний "count_interval"."""
    where = (
        (MessageHistory.repeat_history.is_null(True))
        & (MessageHistory.deleted_at.is_null(True))
        & (
            MessageHistory.created_at
            > (SQL("CURRENT_TIMESTAMP - INTERVAL '%smin'", (count_interval,)))
        )
    )
    if category_id:
        where = (MessageHistory.category == category_id) & where

    subquery = (
        MessageHistory.select(
            MessageHistory.source_media_group_id,
            fn.COUNT("*").alias("amount"),
        )
        .where(where)
        .group_by(MessageHistory.source_media_group_id)
        .alias("t")
    )

    query = MessageHistory.select(
        fn.SUM(
            SQL(
                "CASE WHEN source_media_group_id IS NOT NULL AND source_media_group_id"
                " != '' THEN 1 ELSE t.amount END"
            )
        ).alias("amount")
    ).from_(subquery)

    amount = query.execute()[0].amount
    return int(amount) if amount else 0
