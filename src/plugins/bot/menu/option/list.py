from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from plugins.bot.utils import custom_filters
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/o/$') & custom_filters.admin_only,
)
async def options(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    menu.add_row_button('Администраторы', 'a')
    menu.add_row_button('История фильтра', 'fh')
    menu.add_row_button('История пересылки', 'mh')
    menu.add_row_button('Статистика', 'stat')
    menu.add_row_button('💾 Логи', ':get_logs')

    await callback_query.message.edit_text(
        text='**Параметры**',
        reply_markup=menu.reply_markup,
    )
