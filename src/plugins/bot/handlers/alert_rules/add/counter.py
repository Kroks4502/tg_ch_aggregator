from pyrogram.types import Message

from alerts.counter_rule import add_evaluation_counter_rule_job
from models import AlertRule
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    ACTION_ENTER_THRESHOLD,
    ERROR_INVALID_THRESHOLD,
    NEW_ALERT_RULE_TITLE,
    NEW_COMMON_ALERT_RULE_TITLE,
    QUESTION_COUNT_INTERVAL,
    QUESTION_JOB_INTERVAL,
)
from plugins.bot.handlers.alert_rules.common.utils import (
    get_alert_rule_menu_success_text,
    get_alert_rule_menu_text,
    get_dialog_text,
)
from plugins.bot.menu import Menu
from scheduler import scheduler


@router.page(path=r"/r/:add/counter/")
async def choice_job_interval(menu: Menu):
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

    return await get_alert_rule_menu_text(
        title=NEW_ALERT_RULE_TITLE,
        title_common=NEW_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=category_id,
        rule_type="counter",
        question=QUESTION_JOB_INTERVAL,
    )


@router.page(path=r"/r/:add/counter/job_int/\d+/", back_step=2)
async def choice_count_interval(menu: Menu):
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

    return await get_alert_rule_menu_text(
        title=NEW_ALERT_RULE_TITLE,
        title_common=NEW_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        category_id=category_id,
        rule_type="counter",
        job_interval=job_interval,
        question=QUESTION_COUNT_INTERVAL,
    )


@router.wait_input(back_step=6)
async def add_counter_alert_rule(
    message: Message,
    menu: Menu,
):
    category_id = menu.path.get_value("c")
    job_interval = menu.path.get_value("job_int")
    count_interval = menu.path.get_value("count_int")

    try:
        threshold = int(message.text)
    except ValueError:
        raise ValueError(ERROR_INVALID_THRESHOLD)

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

    return await get_alert_rule_menu_success_text(
        title=NEW_ALERT_RULE_TITLE,
        title_common=NEW_COMMON_ALERT_RULE_TITLE,
        user_id=menu.user.id,
        rule_obj=rule_obj,
        action="добавлено",
    )


@router.page(
    path=r"/r/:add/counter/job_int/\d+/count_int/\d+/",
    back_step=2,
    reply=True,
    add_wait_for_input=add_counter_alert_rule,
)
async def get_threshold(menu: Menu):
    return await get_dialog_text(
        user_id=menu.user.id,
        category_id=menu.path.get_value("c"),
        job_interval=menu.path.get_value("job_int"),
        count_interval=menu.path.get_value("count_int"),
        doing="добавляешь",
        action=ACTION_ENTER_THRESHOLD,
    )
