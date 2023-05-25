import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Source
from plugins.bot.menu.section_filter import list_types_filters
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r's_\d+/:edit/c_\d+/$') & custom_filters.admin_only,
)
async def edit_source_category(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    source_id = int(path.get_value('s'))
    category_obj: Category = Category.get(
        id=int(path.get_value('c', after_action=True))
    )
    source_obj: Source = Source.get(id=source_id)

    q = Source.update({Source.category: category_obj}).where(Source.id == source_id)
    q.execute()
    Source.clear_actual_cache()

    callback_query.data = path.get_prev(2)
    await callback_query.answer('Категория изменена')
    await list_types_filters(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(
        client,
        callback_query,
        (
            'Изменена категория у источника '
            f'{await get_channel_formatted_link(source_obj.tg_id)} '
            f'на {await get_channel_formatted_link(category_obj.tg_id)}'
        ),
    )
