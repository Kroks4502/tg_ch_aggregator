import datetime as dt

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from starter import startup


def start_scheduler():
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    scheduler.add_job(
        func=startup,
        trigger='date',
        run_date=(dt.datetime.today() + dt.timedelta(seconds=1)),
    )
    scheduler.start()
