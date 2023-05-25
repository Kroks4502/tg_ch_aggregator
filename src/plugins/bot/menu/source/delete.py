import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from models import Source
from plugins.bot.menu.source.list import list_source
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r's_\d+/:delete/') & custom_filters.admin_only,
)
async def delete_source(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    source_obj: Source = Source.get(id=int(path.get_value('s')))
    if path.with_confirmation:
        source_obj.delete_instance()
        Source.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Источник удален')
        await list_source(client, callback_query, needs_an_answer=False)

        await send_message_to_admins(
            client,
            callback_query,
            (
                '❌ Удален источник'
                f' **{await get_channel_formatted_link(source_obj.tg_id)}**'
            ),
        )
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        (
            f'Источник: **{await get_channel_formatted_link(source_obj.tg_id)}**\n\n'
            'Ты **удаляешь** источник!'
        ),
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
