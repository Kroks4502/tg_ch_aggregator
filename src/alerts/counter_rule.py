import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from peewee import SQL, fn
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from alerts.common import get_alert_rule_title
from alerts.configs import AlertCounterConfig
from clients import bot
from common import get_message_link, get_words
from models import AlertHistory, AlertRule, MessageHistory

JOB_NAME_TMPL = "counter_alert_rule_{}"
MSG_TEXT_TMPL = "Сработало правило {title}\n\n{messages}"
MAX_WORDS = 10


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
        end_unix_time = int(time.time())
        start_unix_time = end_unix_time - config.count_interval * 60
        await bot.send_message(
            chat_id=alert_rule.user_id,
            text=MSG_TEXT_TMPL.format(
                title=get_alert_rule_title(alert_rule),
                messages=_get_messages(
                    category_id=alert_rule.category_id,
                    start=start_unix_time,
                    end=end_unix_time,
                    last=10,
                ),
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
                                if alert_rule.category_id
                                else f"/r/{alert_rule.id}/?new"
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


def _get_messages(category_id: int, start: int, end: int, last: int):
    mh = MessageHistory.alias()
    mh2 = MessageHistory.alias()
    where = (
        (mh.created_at > fn.TO_TIMESTAMP(start))
        & (mh.created_at < fn.TO_TIMESTAMP(end))
        & (
            (mh.category_media_group_id.is_null())
            | (mh.category_media_group_id.is_null(False))
            & (
                mh.id
                == mh2.select(fn.MIN(mh2.id)).where(
                    mh2.category_media_group_id == mh.category_media_group_id
                )
            )
        )
        & (mh.category_message_id.is_null(False))
        & (mh.repeat_history_id.is_null())
        & (mh.deleted_at.is_null())
    )
    if category_id:
        where = (mh.category_id == category_id) & where

    cte = (
        mh.select()
        .where(where)
        .order_by(mh.created_at.desc())
        # .order_by(mh.created_at)
        .limit(last)
        .cte("mh")
    )

    query = (
        mh.select(
            cte.c.id,
            cte.c.category_id,
            cte.c.category_message_id,
            cte.c.category_media_group_id,
            cte.c.created_at,
            cte.c.data,
            cte.c.source_id,
            cte.c.category_message_rewritten,
        )
        .from_(cte)
        .union(
            mh.select(
                mh.id,
                mh.category_id,
                mh.category_message_id,
                mh.category_media_group_id,
                mh.created_at,
                mh.data,
                mh.source_id,
                mh.category_message_rewritten,
            )
            .from_(mh)
            .join(
                cte,
                on=(cte.c.category_media_group_id == mh.category_media_group_id),
            )
        )
    ).with_cte(cte)

    lines = []
    for row in query:
        line_num = 2 if row.category_message_rewritten else 0
        if short_text := get_short_text(row.data, line=line_num):
            url = get_message_link(
                chat_id=row.category_id,
                message_id=row.category_message_id,
            )
            link = f"**[>>>]({url})**"
            lines.append(f"{short_text} {link}")

    return "\n\n".join(lines)


def get_short_text(data: dict, line: int) -> str:
    if not data or not (message_data := data[0].get("category")):
        return ""

    try:
        message_data.pop("_")
    except KeyError:
        return ""

    message = Message(**message_data)
    text = message.text or message.caption
    if text:
        words = get_words(text=text, line=line)

        return " ".join(words[:MAX_WORDS]).rstrip(".,:;?!\"'`)(") + (
            "…" if len(words) > MAX_WORDS else ""
        )

    return ""
