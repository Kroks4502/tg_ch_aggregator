import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.menu.filter.list import list_filters
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'f_\d+/:delete/') & custom_filters.admin_only,
)
async def delete_filter(client: Client, callback_query: CallbackQuery):
    path = Path(callback_query.data)
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get(id=filter_id)
    if filter_obj.source:
        text = (
            f'Источник: **{await get_channel_formatted_link(filter_obj.source.tg_id)}**'
        )
    else:
        text = '**Общий фильтр**'
    text += (
        f'\nТип фильтра: **{FILTER_TYPES_BY_ID.get(filter_obj.type)}**'
        f'\nПаттерн: `{filter_obj.pattern}`'
    )

    if path.with_confirmation:
        q = Filter.delete().where(Filter.id == filter_id)
        q.execute()

        Filter.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Фильтр удален')
        await list_filters(client, callback_query)

        await send_message_to_admins(
            client, callback_query, f'❌ Удален фильтр:\n{text}'
        )
        return

    text += '\n\nТы **удаляешь** фильтр!'

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        '❌ Подтвердить удаление', callback_data=f'{path}/'
                    ),
                ]
            ]
            + buttons.get_footer(path)
        ),
        disable_web_page_preview=True,
    )
