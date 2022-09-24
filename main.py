import datetime

from pyrogram import compose
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from initialization import bot, user, DEVELOP_MODE
from start_script import startup

scheduler = AsyncIOScheduler()
scheduler.add_job(
    startup, 'date',
    run_date=(datetime.datetime.today() + datetime.timedelta(seconds=1))
)
scheduler.start()

compose([
    bot,
    user,
])
