import logging
from asyncio import sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from clients import bot_client, user_client
from scheduler.jobs.alerts import add_all_evaluation_counter_rule_job
from scheduler.jobs.processing_unread_messages import processing_unread_messages_job
from scheduler.jobs.set_user_bot_as_admin import set_user_bot_as_admin_job
from scheduler.jobs.update_channels_info import update_channels_info_job
from scheduler.jobs.update_users_info import update_users_info_job

scheduler = AsyncIOScheduler()
logger = logging.getLogger("scheduler")


def run_scheduler():
    logger.debug("Running scheduler...")
    scheduler.add_job(func=startup_job, id=startup_job.__name__)
    scheduler.start()
    logger.debug("Scheduler started")


def stop_scheduler():
    logger.debug("Stopping scheduler...")
    if scheduler.running:
        scheduler.shutdown(wait=True)
    logger.debug("Scheduler stopped")


async def startup_job():
    logger.debug("Starting startup job...")
    while (
        not user_client.is_connected
        or not user_client.is_initialized
        or not bot_client.is_connected
        or not bot_client.is_initialized
    ):
        logger.debug("Waiting for clients to be connected...")
        await sleep(1)

    logger.debug("Clients are connected, adding jobs...")
    scheduler.add_job(
        func=set_user_bot_as_admin_job,
        id=f"{set_user_bot_as_admin_job.__name__}_startup",
    )
    scheduler.add_job(
        func=processing_unread_messages_job,
        id=f"{processing_unread_messages_job.__name__}_startup",
    )
    scheduler.add_job(
        func=update_users_info_job,
        id=f"{update_users_info_job.__name__}_startup",
    )
    scheduler.add_job(
        func=update_channels_info_job,
        id=f"{update_channels_info_job.__name__}_startup",
    )

    scheduler.add_job(
        func=processing_unread_messages_job,
        trigger="interval",
        minutes=5,
        id=f"{processing_unread_messages_job.__name__}_interval_5min",
        max_instances=1,
    )
    scheduler.add_job(
        func=update_users_info_job,
        trigger="interval",
        minutes=180,
        id=f"{update_users_info_job.__name__}_interval_180min",
        max_instances=1,
    )
    scheduler.add_job(
        func=update_channels_info_job,
        trigger="interval",
        minutes=180,
        id=f"{update_channels_info_job.__name__}_interval_180min",
        max_instances=1,
    )

    logger.debug("Adding all evaluation counter rule job...")
    add_all_evaluation_counter_rule_job()

    logger.debug("Startup job completed")
