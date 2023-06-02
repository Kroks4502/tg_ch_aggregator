from pyrogram import compose

from clients import bot, user
from config import configure_logging
from scheduler import start_scheduler


def main():
    configure_logging()

    start_scheduler()

    compose([bot, user])


if __name__ == '__main__':
    main()
