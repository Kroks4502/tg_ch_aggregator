from pyrogram import Client

from plugins.bot import router
from plugins.bot.constants.text import QUESTION_EDIT_PAGE
from plugins.bot.handlers.category.common.utils import get_category_menu_text
from plugins.bot.menu import Menu


@router.page(path=r"/c/-\d+/:edit/")
async def edit_category(client: Client, menu: Menu):
    category_id = menu.path.get_value("c")

    menu.add_row_button("Название", "title")
    menu.add_row_button("Описание", "desc")
    menu.add_row_button("Изображение", "photo")

    channel = await client.get_chat(chat_id=category_id)
    return await get_category_menu_text(
        category_id=category_id,
        desc=channel.description,
        question=QUESTION_EDIT_PAGE,
    )
