from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from filter_types import FilterType
from models import Filter
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(filters.regex(r'/f/\d+/$'))
async def detail_filter(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    filter_id = menu.path.get_value('f')
    filter_obj: Filter = Filter.get(filter_id)

    if is_admin(callback_query.from_user.id):
        if filter_obj.type in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            menu.add_row_button('✖️', ':delete')
        else:
            menu.add_row_many_buttons(('📝', ':edit'), ('✖️', ':delete'))

    text = await menu.get_text(filter_obj=filter_obj)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
