from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from plugins.bot.constants import MAIN_MENU_TEXT
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin


def get_main_menu(data: Message | CallbackQuery, path: str = "/") -> Menu:
    menu = Menu(path)

    if is_admin(data.from_user.id):
        menu.add_button.categories()
        menu.add_button.sources()
        menu.add_button.alert_rules(user_id=data.from_user.id)
        menu.add_button.messages_histories()
        menu.add_button.statistics()
        menu.add_button.filters()
        menu.add_button.cleanups()
        menu.add_button.options()

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
