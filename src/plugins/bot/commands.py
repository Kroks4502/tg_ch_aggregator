from pyrogram import Client, filters
from pyrogram.types import Message

from plugins.bot.constants import MAIN_MENU_TEXT
from plugins.bot.menu.main import get_main_menu
from plugins.bot.menu.option.check_post import check_post_waiting_forwarding
from plugins.bot.utils.managers import input_wait_manager


@Client.on_message(filters.command(['start', 'go']))
async def main_menu(_, message: Message):
    menu = get_main_menu(message)

    await message.reply(
        text=MAIN_MENU_TEXT,
        reply_markup=menu.reply_markup,
    )


@Client.on_message(filters.command('check'))
async def check_post(client: Client, message: Message):
    await message.reply(
        'ОК. Ты хочешь проверить есть ли пост в истории.\n\n'
        '**Перешли пост в этот чат и я проверю.**'
    )
    input_wait_manager.add(message.chat.id, check_post_waiting_forwarding, client)
