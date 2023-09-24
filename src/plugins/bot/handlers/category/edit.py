from pyrogram import Client

from models import Category
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/c/-\d+/:edit/")
async def edit_category(client: Client, menu: Menu):
    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    channel = await client.get_chat(chat_id=category_id)

    menu.add_row_button("Название", "name")
    menu.add_row_button("Описание", "desc")
    menu.add_row_button("Изображение", "photo")

    return await menu.get_text(
        category_obj=category_obj,
        last_text=f"Описание: {channel.description}\n\nЧто ты хочешь изменить?",
    )
