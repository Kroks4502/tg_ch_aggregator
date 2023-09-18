from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/:edit/$") & custom_filters.admin_only,
)
async def edit_category(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    channel = await client.get_chat(chat_id=category_id)

    menu.add_row_button("Название", "name")
    menu.add_row_button("Описание", "desc")
    menu.add_row_button("Изображение", "photo")

    await callback_query.message.edit_text(
        text=await menu.get_text(
            category_obj=category_obj,
            last_text=f"Описание: {channel.description}\n\nЧто ты хочешь изменить?",
        ),
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
