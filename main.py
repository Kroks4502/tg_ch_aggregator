import datetime

from pyrogram import compose

from initialization import bot, user
from start_script import startup


from apscheduler.schedulers.asyncio import AsyncIOScheduler

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
