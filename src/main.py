from pyrogram import compose

import db
from clients import bot, user
from scheduler import start_scheduler
from settings import configure_logging


def main():
    configure_logging()

    db.connect()
    db.patch_psycopg2()

    start_scheduler()

    compose([bot, user])


if __name__ == "__main__":
    main()
