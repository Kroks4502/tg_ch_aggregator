import math

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from common import get_message_link, get_shortened_text
from models import Category, CategoryMessageHistory, Source
from plugins.bot.constants import MAX_NUM_ENTRIES_MESSAGE
from plugins.bot.utils import custom_filters
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/mh/\d+/$') & custom_filters.admin_only,
)
async def message_history(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)

    page = menu.path.get_value('mh')

    query = (
        CategoryMessageHistory.select(CategoryMessageHistory, Source, Category)
        .join(Source)
        .switch()
        .join(Category)
        .order_by(CategoryMessageHistory.id.desc())
    )
    obj_counts = query.count()

    text_items = []
    for item in query.paginate(page, MAX_NUM_ENTRIES_MESSAGE):
        text_items.append(
            f'{"🏞" if item.media_group else "🗞"}'
            f'{">📝" if item.source_message_edited else ""}'
            f'{">🗑" if item.source_message_deleted else ""}'
            f' [{get_shortened_text(item.source.title, 30)}]'
            f'({get_message_link(item.source.tg_id, item.source_message_id)})\n'
            f'✅{">🖨" if item.rewritten else ""}'
            f'{">🗑" if item.deleted else ""}'
            f' [{get_shortened_text(item.category.title, 30)}]'
            f'({get_message_link(item.category.tg_id, item.message_id)})\n'
            f'__{item.source_message_id} {item.date.strftime("%Y.%m.%d, %H:%M:%S")}__'
        )

    if page > 1:
        menu.add_row_button('Предыдущие', f'../{"" if page == 1 else page - 1}')
    if page < math.ceil(obj_counts / MAX_NUM_ENTRIES_MESSAGE):
        menu.add_row_button('Следующие', f'../{page + 1}')

    text = (
        '**Последние пересланные сообщения**\n\n'
        + ('\n\n'.join(text_items))
        + f'\n\nВсего записей: **{obj_counts}**'
    )

    await callback_query.message.edit_text(
        text,
        reply_markup=menu.reply_markup,
    )
