import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Source
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import ButtonData, Menu


@Client.on_callback_query(
    filters.regex(r'/c/$'),
)
async def list_category(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    if is_admin(callback_query.from_user.id):
        menu.add_row_button('➕ Добавить категорию', ':add')

    query = (
        Category.select(
            Category.id,
            Category.title,
            peewee.fn.Count(Source.id).alias('amount'),
        )
        .join(Source, peewee.JOIN.LEFT_OUTER)
        .group_by(Category.id)
    )  # Запрашиваем список категорий
    menu.add_rows_from_data(
        data=[ButtonData(i.title, i.id, i.amount) for i in query],
        postfix='s/',
    )

    text = await menu.get_text()
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
