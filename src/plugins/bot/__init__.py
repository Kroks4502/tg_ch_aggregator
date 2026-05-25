from clients import dispatcher
from plugins.bot.menu import Menu  # noqa: F401
from plugins.bot.router import CallbackQueryRouter

router = CallbackQueryRouter(dispatcher=dispatcher)
