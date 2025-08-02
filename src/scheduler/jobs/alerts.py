import logging

from alerts.configs import AlertCounterConfig
from alerts.counter_rule import evaluation_counter_rule_job
from models import AlertRule
from scheduler import run

JOB_NAME_TMPL = "counter_alert_rule_{}"

logger = logging.getLogger(__name__)


def add_all_evaluation_counter_rule_job():
    """Добавить все задачи оценки правил уведомлений на основе количества сообщений."""
    logger.debug("Starting job...")
    for rule_obj in AlertRule.select().where(AlertRule.type == "counter"):
        add_evaluation_counter_rule_job(alert_rule=rule_obj)
    logger.debug("Job completed")


def add_evaluation_counter_rule_job(
    alert_rule: AlertRule,
):
    """Добавить задачу для оценки правила уведомления на основе количества сообщений."""
    logger.debug(f"Adding job for alert rule {alert_rule.id}...")
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
    logger.info(f"Job for alert rule {alert_rule.id} added")


def remove_evaluation_counter_rule_job(
    alert_rule_obj: AlertRule,
):
    """Удалить задачу для оценки правила уведомления на основе количества сообщений."""
    logger.debug(f"Removing job for alert rule {alert_rule_obj.id}...")
    run.scheduler.remove_job(JOB_NAME_TMPL.format(alert_rule_obj.id))
    logger.info(f"Job for alert rule {alert_rule_obj.id} removed")
