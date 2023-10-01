import time

from peewee import SQL, fn

from alerts.configs import AlertCounterConfig, AlertCounterHistory
from common.call_handlers import call_callback_query_handler
from models import AlertHistory, AlertRule, MessageHistory
from plugins.bot.handlers.alert_rules.counter_messages import (
    ALERT_COUNTER_MESSAGES_PATH,
    get_alert_counter_messages,
)


async def evaluation_counter_rule_job(alert_rule: AlertRule):
    """Задача оценки правила уведомления типа счётчик для планировщика."""
    config = AlertCounterConfig(**alert_rule.config)

    amount_messages = _get_amount_messages(
        category_id=alert_rule.category_id,
        count_interval=config.count_interval,
    )
    if amount_messages > config.threshold:
        AlertHistory.create(
            category_id=alert_rule.category_id,
            data=AlertCounterHistory(
                type=alert_rule.type,
                user_id=alert_rule.user_id,
                actual_amount_messages=amount_messages,
                **alert_rule.config,
            ),
            alert_rule_id=alert_rule.id,
        )
        end_ts = int(time.time())
        start_ts = end_ts - config.count_interval * 60

        await call_callback_query_handler(
            func=get_alert_counter_messages,
            user_id=alert_rule.user_id,
            callback_query_data=(
                ALERT_COUNTER_MESSAGES_PATH.format(
                    rule_id=alert_rule.id,
                    start_ts=start_ts,
                    end_ts=end_ts,
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
