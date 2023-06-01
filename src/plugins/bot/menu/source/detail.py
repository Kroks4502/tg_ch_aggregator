from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Source
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import Menu


@Client.on_callback_query(
    filters.regex(r'/s/\d+/$'),
)
async def detail_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    if is_admin(callback_query.from_user.id):
        menu.add_row_many_buttons(
            ('📝', ':edit'),  # Редактировать источник (изменить категорию)
            ('✖️', ':delete'),  # Удалить источник
        )

    menu.add_row_button('Фильтры', 'ft')

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id)
    text = await menu.get_text(source_obj=source_obj)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
