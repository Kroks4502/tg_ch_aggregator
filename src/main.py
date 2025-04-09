from pyrogram import compose

import db
from clients import bot_client, user_client
from scheduler.run import run_scheduler
from settings import configure_logging, IS_ONLY_BOT


def main():
    configure_logging()

    db.connect()
    db.patch_psycopg2()

    if not IS_ONLY_BOT:
        run_scheduler()

    compose([bot_client, user_client])


if __name__ == "__main__":
    main()
