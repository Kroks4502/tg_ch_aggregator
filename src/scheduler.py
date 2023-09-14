from apscheduler.schedulers.asyncio import AsyncIOScheduler

from alerts.counter_rule import add_evaluation_counter_rule_job
from models import AlertRule
from starter import startup

scheduler = AsyncIOScheduler()


def start_scheduler():
    scheduler.add_job(func=startup)

    add_all_evaluation_counter_rule_job()

    scheduler.start()


def add_all_evaluation_counter_rule_job():
    """Добавить все задачи оценки правил уведомлений на основе количества сообщений."""
    for rule_obj in AlertRule.select().where(AlertRule.type == "counter"):
        add_evaluation_counter_rule_job(scheduler=scheduler, alert_rule=rule_obj)
