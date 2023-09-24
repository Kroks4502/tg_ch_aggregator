from pyrogram.types import Message

from alerts.counter_rule import add_evaluation_counter_rule_job
from models import AlertRule, Category
from plugins.bot import router
from plugins.bot.constants import CANCEL
from plugins.bot.handlers.alert_rules.detail import (
    RULE_COUNTER_JOB_INTERVAL_TMPL,
    RULE_TYPE_TMPL,
)
from plugins.bot.menu import Menu
from scheduler import scheduler

RULE_NEW_TEXT = "**Новое правило уведомлений**"
RULE_TYPE_TEXT = f"{RULE_TYPE_TMPL.format('Счётчик сообщений')}"


@router.page(path=r"/r/:add/counter/")
async def add_counter_alert_rule_step_1(menu: Menu):
    menu.add_row_many_buttons(
        ("5m", "job_int/5"),
        ("10m", "job_int/10"),
        ("15m", "job_int/15"),
    )
    menu.add_row_many_buttons(
        ("30m", "job_int/30"),
        ("45m", "job_int/45"),
        ("60m", "job_int/60"),
    )

    category_id = menu.path.get_value("c")
    return await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"{RULE_NEW_TEXT}\n"
            f"{RULE_TYPE_TEXT}\n\n"
            "Как часто будет выполнятся проверка правила?"
        ),
    )


@router.page(path=r"/r/:add/counter/job_int/\d+/", back_step=2)
async def add_counter_alert_rule_step_2(menu: Menu):
    menu.add_row_many_buttons(
        ("5m", "count_int/5"),
        ("10m", "count_int/10"),
        ("15m", "count_int/15"),
    )
    menu.add_row_many_buttons(
        ("30m", "count_int/30"),
        ("60m", "count_int/60"),
    )

    category_id = menu.path.get_value("c")
    job_interval = menu.path.get_value("job_int")
    return await menu.get_text(
        category_obj=Category.get(category_id) if category_id else None,
        last_text=(
            f"{RULE_NEW_TEXT}\n{RULE_TYPE_TEXT}\n{RULE_COUNTER_JOB_INTERVAL_TMPL.format(job_interval)}\n\nВыбери"
            " за сколько последних минут будет выполняться проверка количества"
            " сообщений:"
        ),
    )


@router.wait_input(back_step=6)
async def add_counter_alert_rule_waiting_input(
    message: Message,
    menu: Menu,
):
    category_id = menu.path.get_value("c")
    job_interval = menu.path.get_value("job_int")
    count_interval = menu.path.get_value("count_int")

    try:
        threshold = int(message.text)
    except ValueError:
        raise ValueError("❌ Невалидный порог срабатывания уведомления")

    rule_obj = AlertRule.create(
        user_id=message.from_user.id,
        category_id=category_id,
        type="counter",
        config=dict(
            job_interval=job_interval,
            count_interval=count_interval,
            threshold=threshold,
        ),
    )

    add_evaluation_counter_rule_job(scheduler=scheduler, alert_rule=rule_obj)

    return (
        "✅ Правило уведомления "
        f"с проверкой раз в {job_interval} мин., "
        f"окном проверки {count_interval} мин. "
        f"и порогом срабатывания `{threshold}` шт. добавлено"
    )


@router.page(
    path=r"/r/:add/counter/job_int/\d+/count_int/\d+/",
    back_step=2,
    reply=True,
    add_wait_for_input=add_counter_alert_rule_waiting_input,
)
async def add_counter_alert_rule_step_3(menu: Menu):
    job_interval = menu.path.get_value("job_int")
    count_interval = menu.path.get_value("count_int")
    return (
        "ОК. Ты добавляешь новое правило уведомления с проверкой раз в"
        f" {job_interval} мин. и окном проверки {count_interval} мин.\n\n**Введи"
        f" количество сообщений для срабатывания уведомления** или {CANCEL}"
    )
