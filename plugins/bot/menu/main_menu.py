from pyrogram import Client, filters
from pyrogram.types import (Message, CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup)

from log import logger
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.section_category import list_category_buttons


def main_menu(data: Message | CallbackQuery) -> (str, list[list]):
    path = Path('/')

    text = '**Агрегатор каналов**'

    inline_keyboard = list_category_buttons(path, f'📚 Все источники')

    if is_admin(data.from_user.id):
        inline_keyboard.append([InlineKeyboardButton(
            '➕ Добавить категорию',
            callback_data=path.add_action('add')
        ), ])

    inline_keyboard.append([InlineKeyboardButton(
        f'🔘 Общие фильтры',
        callback_data=path.add_value('s', 0)
    )])

    return text, inline_keyboard


@Client.on_callback_query(filters.regex(
    r'^/$'))
async def set_main_menu(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    text, inline_keyboard = main_menu(callback_query)
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_message(filters.command('go'))
async def send_main_menu(_, message: Message):
    text, inline_keyboard = main_menu(message)
    await message.reply(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))
