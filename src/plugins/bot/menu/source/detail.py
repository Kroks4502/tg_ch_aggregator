from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Filter, Source
from plugins.bot.utils.chat_warnings import get_chat_warnings
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import Menu


@Client.on_callback_query(
    filters.regex(r'/s/\d+/$'),
)
async def detail_source(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id)

    last_text = ''
    if is_admin(callback_query.from_user.id):
        menu.add_row_many_buttons(
            ('📝', ':edit'),  # Редактировать источник (изменить категорию)
            ('✖️', ':delete'),  # Удалить источник
        )
        last_text = await get_chat_warnings(source_obj)

    count = Filter.select().where(Filter.source == source_obj).count()
    menu.add_row_button('🪤 Фильтры' + (f' ({count})' if count else ''), 'ft')

    count = len(source_obj.cleanup_regex)
    menu.add_row_button('🧹 Очистка' + (f' ({count})' if count else ''), 'cl')

    if source_obj.is_rewrite:
        menu.add_row_button('Пересылать', ':off_rewrite')
    else:
        menu.add_row_button('Перепечатывать', ':on_rewrite')

    text = await menu.get_text(source_obj=source_obj, last_text=last_text)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
