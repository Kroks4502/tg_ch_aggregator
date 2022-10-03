from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup

from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_category import main_menu
from plugins.bot.menu.section_option import check_post_waiting_forwarding


@Client.on_message(filters.command('go'))
async def send_main_menu(_, message: Message):
    text, inline_keyboard = main_menu(message)
    await message.reply(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_message(filters.command('check'))
async def send_main_menu(client: Client, message: Message):
    chat_id = message.chat.id

    text = ('ОК. Ты хочешь проверить есть ли пост в истории.\n\n'
            '**Перешли пост в этот чат и я проверю.**')

    await message.reply(text)
    input_wait_manager.add(
        chat_id, check_post_waiting_forwarding, client)
