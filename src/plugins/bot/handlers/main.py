from pyrogram import Client
from pyrogram.types import Message

from models import GlobalSettings
from plugins.bot import input_wait_manager, router
from plugins.bot.constants.commands import CANCEL_TEXT, START_TEXT
from plugins.bot.constants.text import MAIN_MENU_TEXT
from plugins.bot.menu import Menu


@router.command(commands=[START_TEXT, CANCEL_TEXT])
async def main_menu_by_command(client: Client, message: Message, menu: Menu):
    try:
        input_wait_manager.remove(client=client, chat_id=message.chat.id)
    except KeyError:
        pass

    _set_main_menu_buttons(menu)
    return MAIN_MENU_TEXT


@router.page(path=r"^/", admin_only=False)
async def main_menu_by_button(menu: Menu):
    _set_main_menu_buttons(menu)
    return MAIN_MENU_TEXT


def _set_main_menu_buttons(menu: Menu):
    if menu.is_admin_user():
        menu.add_button.categories()
        menu.add_button.sources()
        menu.add_button.alert_rules(user_id=menu.user.id)
        menu.add_button.messages_histories()
        menu.add_button.statistics()
        menu.add_button.filters()

        amount_cleanups = GlobalSettings.get(key="cleanup_list").value
        menu.add_button.cleanups(amount=len(amount_cleanups))

        menu.add_button.options()


@router.page(path=r"·/", admin_only=False)
async def empty():
    """Обработчик для пустой кнопки"""
