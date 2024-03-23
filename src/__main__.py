import contextlib
import logging
import sys

import db
from clients import bot_client, user_client

# from plugins import example_echo, message_and_albums
from plugins.user.sources_monitoring import new_message

# from scheduler.run import run_scheduler
from settings import configure_logging

logger = logging.getLogger(__name__)

configure_logging()

db.connect()
db.patch_psycopg2()

# run_scheduler()

# try:
#     logger.info("Starting Userbot")
#     client.loop.run_until_complete(setup_bot())
#     logger.info("TG Bot Startup Completed")
# except Exception as e:
#     logger.critical(f"{e}")
#     sys.exit()


async def clients_info():
    user_info = await user_client.get_me()
    bot_info = await bot_client.get_me()

    print(user_info.stringify())
    print(bot_info.stringify())


user_client.loop.run_until_complete(clients_info())


if len(sys.argv) in {1, 3, 4}:
    with contextlib.suppress(ConnectionError):
        user_client.run_until_disconnected()
else:
    user_client.disconnect()
