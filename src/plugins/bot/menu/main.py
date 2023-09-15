from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from plugins.bot.constants import ALERT_BTN_TEXT, MAIN_MENU_TEXT
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import Menu


def get_main_menu(data: Message | CallbackQuery, path: str = "/") -> Menu:
    menu = Menu(path)

    if is_admin(data.from_user.id):
        menu.add_row_button("🗂 Категории", "c")
        menu.add_row_button("📚 Источники", "s")
        menu.add_row_button("🪤 Фильтры", "ft")
        menu.add_row_button("🧹 Очистка", "cl")
        menu.add_row_button(ALERT_BTN_TEXT, "r")
        # menu.add_row_button("🚧 Проверить пост", ":check_post")
        menu.add_row_button("🛠 Настройки", "o")

    return menu


@Client.on_callback_query(
    filters.regex(r"^/(\?new|)$"),
)
async def set_main_menu(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = get_main_menu(callback_query, path=callback_query.data)

    if menu.need_send_new_message:
        await client.send_message(
            chat_id=callback_query.message.chat.id,
            text=MAIN_MENU_TEXT,
            reply_markup=menu.reply_markup,
        )
        return

    await callback_query.message.edit_text(
        text=MAIN_MENU_TEXT,
        reply_markup=menu.reply_markup,
    )


@Client.on_callback_query(
    filters.regex(r"·/$"),
)
async def empty_button(_, callback_query: CallbackQuery):
    """Пустая кнопка для пагинации"""
    await callback_query.answer()
