from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from plugins.bot.constants import MAIN_MENU_TEXT
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import Menu


def get_main_menu(data: Message | CallbackQuery) -> Menu:
    menu = Menu('/')

    if is_admin(data.from_user.id):
        menu.add_row_button('🗂 Категории', 'c')
        # menu.add_row_button('📚 Все источники', 's')  # todo pagination
        menu.add_row_button('🪤 Общие фильтры', 'ft')
        menu.add_row_button('🧹 Общая очистка', 'cl')
        menu.add_row_button('🚧 Проверить пост', ':check_post')
        menu.add_row_button('🛠 Настройки', 'o')

    return menu


@Client.on_callback_query(
    filters.regex(r'^/$'),
)
async def set_main_menu(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = get_main_menu(callback_query)

    await callback_query.message.edit_text(
        text=MAIN_MENU_TEXT,
        reply_markup=menu.reply_markup,
    )
