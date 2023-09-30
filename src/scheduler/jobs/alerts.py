from alerts.configs import AlertCounterConfig
from alerts.counter_rule import evaluation_counter_rule_job
from models import AlertRule
from scheduler import run

JOB_NAME_TMPL = "counter_alert_rule_{}"


def add_all_evaluation_counter_rule_job():
    """Добавить все задачи оценки правил уведомлений на основе количества сообщений."""
    for rule_obj in AlertRule.select().where(AlertRule.type == "counter"):
        add_evaluation_counter_rule_job(alert_rule=rule_obj)


def add_evaluation_counter_rule_job(
    alert_rule: AlertRule,
):
    """Добавить задачу для оценки правила уведомления на основе количества сообщений."""
    config = AlertCounterConfig(**alert_rule.config)

    async def job():
        await evaluation_counter_rule_job(alert_rule)

    job_name = JOB_NAME_TMPL.format(alert_rule.id)
    run.scheduler.add_job(
        func=job,
        trigger="interval",
        minutes=config.job_interval,
        id=job_name,
        name=job_name,
        max_instances=1,
    )


def remove_evaluation_counter_rule_job(
    alert_rule_obj: AlertRule,
):
    """Удалить задачу для оценки правила уведомления на основе количества сообщений."""
    run.scheduler.remove_job(JOB_NAME_TMPL.format(alert_rule_obj.id))
