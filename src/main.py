import asyncio
import logging
import signal
import sys

import db
from clients import aiogram_bot, dispatcher, user_client
from common.notifier_registry import (
    set_admin_notifier,
    set_alert_notifier,
    set_user_error_notifier,
)
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

    register_notifiers()
    # Forces import of all bot handlers (decorator side-effects register
    # them in aiogram Dispatcher). Pyrogram больше не загружает их через
    # plugins=dict(root="plugins.bot"), потому что bot_client не стартует.
    _load_bot_handlers()

    if not IS_ONLY_BOT:
        run_scheduler()

    tasks: list[asyncio.Task] = [
        asyncio.create_task(dispatcher.start_polling(aiogram_bot)),
    ]
    if not IS_ONLY_BOT:
        tasks.append(asyncio.create_task(_run_user_client()))

    await asyncio.gather(*tasks)


async def _run_user_client():
    await user_client.start()
    # Pyrogram'у нужен живой event loop пока user_client работает.
    # idle() блокирует до получения SIGTERM/SIGINT.
    from pyrogram import idle

    await idle()


def register_notifiers():
    """
    Зарегистрировать реализации notifier-контрактов в общем реестре.
    """
    from plugins.bot.notifiers import (
        admin_notifier,
        alert_notifier,
        user_error_notifier,
    )

    set_admin_notifier(admin_notifier)
    set_alert_notifier(alert_notifier)
    set_user_error_notifier(user_error_notifier)


def _load_bot_handlers():
    """
    Импортирует все модули в plugins/bot/handlers — их декораторы
    @router.page / .wait_input / .command регистрируются в Dispatcher как
    side-effect. До PR-2 это делал pyrogram через plugins=dict(root=...).
    """
    import pkgutil

    import plugins.bot.handlers as h_pkg

    for _, name, _ in pkgutil.walk_packages(h_pkg.__path__, h_pkg.__name__ + "."):
        __import__(name)


def shutdown_handler(signum, _frame):
    logger.debug("Received signal %s", signum)

    if not IS_ONLY_BOT:
        logger.debug("Stopping scheduler...")
        stop_scheduler()
        logger.info("Scheduler stopped")

    logger.debug("Stopping aiogram dispatcher polling...")
    asyncio.run(dispatcher.stop_polling())
    asyncio.run(aiogram_bot.session.close())
    logger.info("Aiogram dispatcher stopped")

    if not IS_ONLY_BOT:
        logger.debug("Stopping user_client...")
        asyncio.run(user_client.stop())
        logger.info("user_client stopped")

    logger.debug("Closing database connection...")
    db.close_connection()
    logger.info("Database connection closed")

    logger.info("Application stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
