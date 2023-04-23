import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import compose

from clients import bot, user
from starter import startup

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
scheduler.add_job(
    func=startup,
    trigger='date',
    run_date=(datetime.datetime.today() + datetime.timedelta(seconds=1))
)
scheduler.start()

compose([
    bot,
    user,
])
