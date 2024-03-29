from asyncio import sleep

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from clients import bot_client, user_client
from scheduler.jobs.alerts import add_all_evaluation_counter_rule_job
from scheduler.jobs.processing_unread_messages import processing_unread_messages_job
from scheduler.jobs.set_user_bot_as_admin import set_user_bot_as_admin_job
from scheduler.jobs.update_admins_info import update_users_info_job
from scheduler.jobs.update_channels_info import update_channels_info_job

scheduler = AsyncIOScheduler()


async def startup_job():
    while (
        not user_client.is_connected
        or not user_client.is_initialized
        or not bot_client.is_connected
        or not bot_client.is_initialized
    ):
        await sleep(1)

    scheduler.add_job(
        func=set_user_bot_as_admin_job,
        id=set_user_bot_as_admin_job.__name__,
    )
    scheduler.add_job(
        func=processing_unread_messages_job,
        id=processing_unread_messages_job.__name__,
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
        func=update_users_info_job,
        trigger="interval",
        minutes=60,
        id=update_users_info_job.__name__,
        max_instances=1,
    )
    scheduler.add_job(
        func=update_channels_info_job,
        trigger="interval",
        minutes=60,
        id=update_channels_info_job.__name__,
        max_instances=1,
    )

    add_all_evaluation_counter_rule_job()


def run_scheduler():
    scheduler.add_job(func=startup_job, id=startup_job.__name__)
    scheduler.start()
