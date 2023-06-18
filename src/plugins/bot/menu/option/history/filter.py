import math

from peewee import JOIN
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from common import get_message_link, get_shortened_text
from filter_types import FILTER_TYPES_BY_ID
from models import Filter, MessageHistory, Source
from plugins.bot.constants import MAX_NUM_ENTRIES_MESSAGE
from plugins.bot.utils import custom_filters
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/fh/\d+/$') & custom_filters.admin_only,
)
async def filter_history(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)

    page = menu.path.get_value('fh')

    source_filter = Source.alias()
    query = (
        MessageHistory.select(MessageHistory, Source, Filter, source_filter)
        .join(Source, JOIN.LEFT_OUTER)
        .switch()
        .join(Filter)
        .join(source_filter, JOIN.LEFT_OUTER)
        .order_by(MessageHistory.id.desc())
    )
    obj_counts = query.count()

    text_items = []
    for f in query.paginate(page, MAX_NUM_ENTRIES_MESSAGE):
        text_items.append(
            f'{"🏞" if f.source_media_group else "🗞"}'
            f'[{get_shortened_text(f.source.title, 30)}]'
            f'({get_message_link(f.source_id, f.source_message_id)})\n'
            f'**{"П" if f.filter.source else "O"}** '
            f'**{FILTER_TYPES_BY_ID.get(f.filter.type)}** '
            f'`{f.filter.pattern}`\n'
            f'__{f.source_message_id} {f.created_at.strftime("%Y.%m.%d, %H:%M:%S")}__'
        )

    if page > 1:
        menu.add_row_button('Предыдущие', f'../{"" if page == 1 else page - 1}')
    if page < math.ceil(obj_counts / MAX_NUM_ENTRIES_MESSAGE):
        menu.add_row_button('Следующие', f'../{page + 1}')

    text = (
        '**Последние отфильтрованные сообщения**\n\n'
        + ('\n\n'.join(text_items))
        + f'\n\nВсего записей: **{obj_counts}**'
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
    )
