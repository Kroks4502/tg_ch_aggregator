from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import GlobalSettings, Source
from plugins.bot.constants import ADD_BNT_TEXT
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/cl/$'),
)
async def list_cleanup(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data)

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj and is_admin(callback_query.from_user.id):
        cleanup_regex = source_obj.cleanup_regex
    else:
        cleanup_regex = GlobalSettings.get(key='cleanup_regex').value
    menu.add_row_button(ADD_BNT_TEXT, ':add')

    for idx, reg in enumerate(cleanup_regex):
        menu.add_row_button(reg, str(idx))

    text = await menu.get_text(
        source_obj=source_obj,
        last_text='**Очистка текста**' if source_obj else '**Общая очистка текста**',
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
