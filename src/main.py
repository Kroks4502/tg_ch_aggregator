import asyncio
import logging
import signal
import sys

from pyrogram import compose

import db
from clients import bot_client, user_client
from scheduler.run import run_scheduler, stop_scheduler
from settings import IS_ONLY_BOT, check_required_env_vars, configure_logging

logger = logging.getLogger(__name__)


def main():
    configure_logging()
    check_required_env_vars()

    logger.info("Starting application...")
    try:
        logger.debug("Getting event loop...")
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Event loop not found, creating new one...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        logger.debug("Event loop created")

    logger.debug("Running startup coroutine...")
    loop.run_until_complete(startup())


async def startup():
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    db.connect()
    db.patch_psycopg2()

    if not IS_ONLY_BOT:
        run_scheduler()

    await compose([bot_client, user_client])


def shutdown_handler(signum, _frame):
    logger.debug("Received signal %s", signum)

    if not IS_ONLY_BOT:
        logger.debug("Stopping scheduler...")
        stop_scheduler()
        logger.info("Scheduler stopped")

    logger.debug("Stopping telegram clients...")
    asyncio.run(bot_client.stop())
    asyncio.run(user_client.stop())
    logger.info("Telegram clients stopped")

    logger.debug("Closing database connection...")
    db.close_connection()
    logger.info("Database connection closed")

    logger.info("Application stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
