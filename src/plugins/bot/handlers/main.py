from datetime import datetime

from aiogram.types import Message
from aiogram.types import User as AiogramUser
from peewee import DoesNotExist

from models import GlobalSettings, User
from plugins.bot import router
from plugins.bot.constants.commands import CANCEL_TEXT, START_TEXT
from plugins.bot.constants.text import MAIN_MENU_TEXT
from plugins.bot.menu import Menu


@router.command(commands=[START_TEXT, CANCEL_TEXT])
async def main_menu_by_command(message: Message, menu: Menu):
    _update_or_create_user(message.from_user)
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


def _update_or_create_user(user: AiogramUser):
    try:
        user_obj = User.get(id=user.id)
        user_obj.last_interaction_at = datetime.now()
        user_obj.save()
    except DoesNotExist:
        User.create(id=user.id, username=user.username or str(user.id))


@router.page(path=r"·/", admin_only=False)
async def empty():
    """Обработчик для пустой кнопки"""
