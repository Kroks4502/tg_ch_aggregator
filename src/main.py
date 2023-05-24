from pyrogram import compose

from clients import bot, user
from config import configure_logging
from scheduler import start_scheduler

configure_logging()

start_scheduler()

compose([
    bot,
    user,
])
