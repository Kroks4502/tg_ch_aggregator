from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from alerts.counter_rule import add_evaluation_counter_rule_job
from models import AlertRule, Category
from plugins.bot.constants import CANCEL
from plugins.bot.menu.category.alert_rules.detail import (
    RULE_COUNTER_JOB_INTERVAL_TMPL,
    RULE_TYPE_TMPL,
)
from plugins.bot.utils import custom_filters
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu
from scheduler import scheduler

RULE_NEW_TEXT = "**Новое правило уведомлений**"
RULE_TYPE_TEXT = f"{RULE_TYPE_TMPL.format('Счётчик сообщений')}"


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/:add/counter/$") & custom_filters.admin_only,
)
async def add_counter_alert_rule_step_1(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
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
    text = await menu.get_text(
        category_obj=Category.get(category_id),
        last_text=(
            f"{RULE_NEW_TEXT}\n"
            f"{RULE_TYPE_TEXT}\n\n"
            "Как часто будет выполнятся проверка правила?"
        ),
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/:add/counter/job_int/\d+/$") & custom_filters.admin_only,
)
async def add_counter_alert_rule_step_2(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)
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
    text = await menu.get_text(
        category_obj=Category.get(category_id),
        last_text=(
            f"{RULE_NEW_TEXT}\n{RULE_TYPE_TEXT}\n{RULE_COUNTER_JOB_INTERVAL_TMPL.format(job_interval)}\n\nВыбери"
            " за сколько последних минут будет выполняться проверка количества"
            " сообщений:"
        ),
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/:add/counter/job_int/\d+/count_int/\d+/$")
    & custom_filters.admin_only,
)
async def add_counter_alert_rule_step_3(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)
    job_interval = menu.path.get_value("job_int")
    count_interval = menu.path.get_value("count_int")
    await callback_query.message.reply(
        "ОК. Ты добавляешь новое правило уведомления с проверкой раз в"
        f" {job_interval} мин. и окном проверки {count_interval} мин.\n\n**Введи"
        f" количество сообщений для срабатывания уведомления** или {CANCEL}"
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        add_counter_alert_rule_waiting_input,
        client,
        callback_query,
    )


async def add_counter_alert_rule_waiting_input(
    _,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data, back_step=6)

    category_id = menu.path.get_value("c")
    job_interval = menu.path.get_value("job_int")
    count_interval = menu.path.get_value("count_int")

    async def reply(t):
        await message.reply_text(
            text=t,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    try:
        threshold = int(message.text)
    except ValueError:
        await reply("❌ Невалидный порог срабатывания уведомления")
        return

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

    text = (
        "✅ Правило уведомления "
        f"с проверкой раз в {job_interval} мин., "
        f"окном проверки {count_interval} мин. "
        f"и порогом срабатывания `{threshold}` шт. добавлено"
    )
    await reply(text)
