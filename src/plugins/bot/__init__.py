from clients import bot
from plugins.bot.menu import Menu  # noqa: F401
from plugins.bot.router import CallbackQueryRouter
from utils.input_wait_manager import InputWaitManager

input_wait_manager = InputWaitManager()
router = CallbackQueryRouter(client=bot, input_wait_manager=input_wait_manager)
