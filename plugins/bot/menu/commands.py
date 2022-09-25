from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup

from plugins.bot.menu.section_category import main_menu


@Client.on_message(filters.command('go'))
async def send_main_menu(_, message: Message):
    text, inline_keyboard = main_menu(message)
    await message.reply(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
