from pyrogram import compose

from clients import bot, user
from config import configure_logging, DEVELOP_MODE
from scheduler import start_scheduler


def main():
    configure_logging()

    if not DEVELOP_MODE:
        start_scheduler()

    compose([bot, user])


if __name__ == '__main__':
    main()
