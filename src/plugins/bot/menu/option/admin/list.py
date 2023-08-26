from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Admin
from plugins.bot.constants import ADD_BNT_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.menu import ButtonData, Menu


@Client.on_callback_query(
    filters.regex(r'/a/(p/\d+/|)$') & custom_filters.admin_only,
)
async def list_admins(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    menu.add_row_button(ADD_BNT_TEXT, ':add')

    query = Admin.select(
        Admin.id,
        Admin.username,
    )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.username, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    await callback_query.message.edit_text(
        text='**Список администраторов:**',
        reply_markup=menu.reply_markup,
    )
