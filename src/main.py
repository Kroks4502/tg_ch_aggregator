import asyncio
import signal
import sys

from pyrogram import compose

import db
from clients import bot_client, user_client
from scheduler.run import run_scheduler, stop_scheduler
from settings import IS_ONLY_BOT, configure_logging


def signal_handler(_signum, _frame):
    if not IS_ONLY_BOT:
        stop_scheduler()
    asyncio.run(bot_client.stop())
    asyncio.run(user_client.stop())
    db.close_connection()

    sys.exit(0)


def main():
    configure_logging()

    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    db.connect()
    db.patch_psycopg2()

    if not IS_ONLY_BOT:
        run_scheduler()

    compose([bot_client, user_client])


if __name__ == "__main__":
    main()
