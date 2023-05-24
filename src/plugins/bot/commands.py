from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, Message

from plugins.bot.menu.section_category import main_menu
from plugins.bot.menu.section_option import check_post_waiting_forwarding
from plugins.bot.menu.utils.managers import input_wait_manager


@Client.on_message(filters.command(['start', 'go']))
async def send_main_menu(_, message: Message):
    text, inline_keyboard = main_menu(message)
    await message.reply(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_message(filters.command('check'))
async def send_check(client: Client, message: Message):
    await message.reply(
        'ОК. Ты хочешь проверить есть ли пост в истории.\n\n'
        '**Перешли пост в этот чат и я проверю.**')
    input_wait_manager.add(
        message.chat.id, check_post_waiting_forwarding, client)
