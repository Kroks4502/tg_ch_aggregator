from apscheduler.schedulers.asyncio import AsyncIOScheduler
from peewee import SQL, fn
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from alerts.common import get_alert_rule_title
from alerts.configs import AlertCounterConfig
from clients import bot
from models import AlertHistory, AlertRule, MessageHistory
from plugins.bot.utils.links import get_channel_formatted_link

JOB_NAME_TMPL = "counter_alert_rule_{}"
MSG_TEXT_TMPL = "Сработало правило {title}\n\nКатегория: **{link}**"


def add_evaluation_counter_rule_job(
    scheduler: AsyncIOScheduler,
    alert_rule: AlertRule,
):
    """Добавить задачу для оценки правила уведомления на основе количества сообщений."""
    config = AlertCounterConfig(**alert_rule.config)

    async def job():
        await _evaluation_counter_rule_job(alert_rule)

    job_name = JOB_NAME_TMPL.format(alert_rule.id)
    scheduler.add_job(
        func=job,
        trigger="interval",
        minutes=config.job_interval,
        id=job_name,
        name=job_name,
    )


def remove_evaluation_counter_rule_job(
    scheduler: AsyncIOScheduler,
    alert_rule_obj: AlertRule,
):
    """Удалить задачу для оценки правила уведомления на основе количества сообщений."""
    scheduler.remove_job(JOB_NAME_TMPL.format(alert_rule_obj.id))


async def _evaluation_counter_rule_job(alert_rule: AlertRule):
    """Задача оценки правила уведомления типа счётчик для планировщика."""
    config = AlertCounterConfig(**alert_rule.config)

    amount_messages = _get_amount_messages(
        category_id=alert_rule.category_id,
        count_interval=config.count_interval,
    )
    if amount_messages > config.threshold:
        # end_unix_time = int(time.time())
        # start_unix_time = end_unix_time - config.count_interval * 60
        await bot.send_message(
            chat_id=alert_rule.user_id,
            text=MSG_TEXT_TMPL.format(
                title=get_alert_rule_title(alert_rule),
                link=await get_channel_formatted_link(alert_rule.category_id),
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    # [
                    #     InlineKeyboardButton(
                    #         text="Последние 5 сообщений",
                    #         callback_data=(
                    #             f"/c/{alert_rule.category_id}/start/{start_unix_time}/end/{end_unix_time}/last/5/"
                    #         ),
                    #     )
                    # ],
                    [
                        InlineKeyboardButton(
                            text="Правило уведомления",
                            callback_data=(
                                f"/c/{alert_rule.category_id}/r/{alert_rule.id}/?new"
                            ),
                        )
                    ],
                ]
            ),
            disable_web_page_preview=True,
        )
        AlertHistory.create(
            category_id=alert_rule.category_id,
            data={
                "type": alert_rule.type,
                "user_id": alert_rule.user_id,
                **alert_rule.config,
                "actual_amount_messages": amount_messages,
            },
        )


def _get_amount_messages(category_id: int, count_interval: int) -> int:
    """Получить количество сообщений в категории за последний "count_interval"."""
    subquery = (
        MessageHistory.select(
            MessageHistory.source_media_group_id,
            fn.COUNT("*").alias("amount"),
        )
        .where(
            (MessageHistory.category == category_id)
            & (MessageHistory.repeat_history.is_null(True))
            & (MessageHistory.deleted_at.is_null(True))
            & (
                MessageHistory.created_at
                > (SQL("CURRENT_TIMESTAMP - INTERVAL '%smin'", (count_interval,)))
            )
        )
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
