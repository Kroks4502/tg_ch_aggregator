from peewee import JOIN
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from common import get_message_link, get_shortened_text
from filter_types import FILTER_TYPES_BY_ID
from models import Filter, MessageHistory, Source
from plugins.bot.constants import DEFAULT_NUM_ITEMS_ON_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/fh/(p/\d+/|)$') & custom_filters.admin_only,
)
async def filter_history(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    source_filter = Source.alias()
    query = (
        MessageHistory.select(MessageHistory, Source, Filter, source_filter)
        .join(Source, JOIN.LEFT_OUTER)
        .switch()
        .join(Filter)
        .join(source_filter, JOIN.LEFT_OUTER)
        .order_by(MessageHistory.id.desc())
    )

    start_text = ''
    if source_id := menu.path.get_value('s'):
        src_link = await get_channel_formatted_link(source_id)
        start_text = f' источника {src_link}'
        query = query.where(Source.id == source_id)
    elif category_id := menu.path.get_value('c'):
        cat_link = await get_channel_formatted_link(category_id)
        start_text = f' категории {cat_link}'
        query = query.where(Source.category_id == category_id)

    pagination = menu.set_pagination(
        total_items=query.count(),
        size=DEFAULT_NUM_ITEMS_ON_TEXT,
    )

    text_items = []
    for f in query.paginate(pagination.page, pagination.size):
        text_items.append(
            f'{"🏞" if f.source_media_group_id else "🗞"}'
            f'[{get_shortened_text(f.source.title, 30)}]'
            f'({get_message_link(f.source_id, f.source_message_id)})\n'
            f'**{"П" if f.filter.source else "O"}** '
            f'**{FILTER_TYPES_BY_ID.get(f.filter.type)}** '
            f'`{f.filter.pattern}`\n'
            f'__{f.source_message_id} {f.created_at.strftime("%Y.%m.%d, %H:%M:%S")}__'
        )

    text = (
        f'**Отфильтрованные сообщения{start_text}**\n\n'
        + ('\n\n'.join(text_items))
        + f'\n\nВсего: **{pagination.total_items}**'
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
