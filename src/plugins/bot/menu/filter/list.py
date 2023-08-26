from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Filter, Source
from plugins.bot.constants import ADD_BNT_TEXT
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import ButtonData, Menu


@Client.on_callback_query(
    filters.regex(r'/ft/\d+/f/(p/\d+/|)$'),
)
async def list_filters(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)

    filter_type_id = menu.path.get_value('ft')
    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id) if source_id else None

    if is_admin(callback_query.from_user.id):
        menu.add_row_button(ADD_BNT_TEXT + ' фильтр', ':add')

    if source_obj:
        query = Filter.select().where(
            (Filter.source == source_id) & (Filter.type == filter_type_id)
        )
    else:
        query = Filter.select().where(
            Filter.source.is_null(True) & (Filter.type == filter_type_id)
        )

    pagination = menu.set_pagination(total_items=query.count())
    menu.add_rows_from_data(
        data=[
            ButtonData(i.pattern, i.id, 0)
            for i in query.paginate(pagination.page, pagination.size)
        ],
    )

    text = await menu.get_text(source_obj=source_obj, filter_type_id=filter_type_id)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
