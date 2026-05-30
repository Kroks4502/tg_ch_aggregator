import asyncio
import logging
import signal
import sys

import db
from clients import aiogram_bot, dispatcher, telethon_user_client
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
    # Импортирует все handler-модули — декораторы @router.page/.wait_input/.command
    # регистрируются в aiogram Dispatcher как side-effect.
    _load_bot_handlers()

    if not IS_ONLY_BOT:
        run_scheduler()

    tasks: list[asyncio.Task] = [
        asyncio.create_task(dispatcher.start_polling(aiogram_bot, handle_signals=False)),
    ]
    if not IS_ONLY_BOT:
        tasks.append(asyncio.create_task(_run_userbot()))

    await asyncio.gather(*tasks)


async def _run_userbot():
    """Запустить Telethon userbot и зарегистрировать обработчики событий."""
    async with telethon_user_client:
        _register_telethon_handlers(telethon_user_client)
        logger.info("Telethon userbot connected")
        await telethon_user_client.run_until_disconnected()


def _register_telethon_handlers(client):
    """Явная регистрация обработчиков Telethon (вместо pyrogram plugins=dict(root=...))."""
    from telethon import events

    from plugins.user.sources_monitoring.deleted_messages import on_deleted_messages
    from plugins.user.sources_monitoring.edited_message import on_edited_message
    from plugins.user.sources_monitoring.new_message import on_new_message
    from plugins.user.sources_monitoring.service_message import on_service_message

    # Сообщения из источников (не сервисные)
    client.add_event_handler(
        on_new_message,
        events.NewMessage(func=lambda e: not e.message.action),
    )
    # Редактирование
    client.add_event_handler(
        on_edited_message,
        events.MessageEdited(func=lambda e: not e.message.action),
    )
    # Удаление (Telethon не поддерживает func= для MessageDeleted — фильтруем внутри)
    client.add_event_handler(on_deleted_messages, events.MessageDeleted())
    # Сервисные сообщения (pin, join, leave)
    client.add_event_handler(
        on_service_message,
        events.NewMessage(func=lambda e: bool(e.message.action)),
    )


def register_notifiers():
    """Зарегистрировать реализации notifier-контрактов в общем реестре."""
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
    side-effect.
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

    logger.debug("Closing database connection...")
    db.close_connection()
    logger.info("Database connection closed")

    logger.info("Application stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
