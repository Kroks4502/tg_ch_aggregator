from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import GlobalSettings, Source
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import Menu


@Client.on_callback_query(
    filters.regex(r'/cl/\d+/$'),
)
async def detail_cleanup_regex(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    cleanup_id = menu.path.get_value('cl')

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj:
        pattern = source_obj.cleanup_regex[cleanup_id]
    else:
        cleanup_regex = GlobalSettings.get(key='cleanup_regex').value
        pattern = cleanup_regex[cleanup_id]

    if is_admin(callback_query.from_user.id):
        menu.add_row_many_buttons(('📝', ':edit'), ('✖️', ':delete'))

    text = await menu.get_text(source_obj=source_obj, cleanup_pattern=pattern)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
