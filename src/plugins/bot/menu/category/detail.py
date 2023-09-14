from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from plugins.bot.menu.source.list import list_source


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/$"),
)
async def detail_category(_, callback_query: CallbackQuery):
    # Redirect to list_source
    callback_query.data += "s/"
    await list_source(_, callback_query)
