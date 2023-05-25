import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from models import Category, Source, Filter
from plugins.bot.menu.main import set_main_menu
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'c_\d+/:delete/') & custom_filters.admin_only,
)
async def delete_category(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    category_obj: Category = Category.get(id=int(path.get_value('c')))
    if path.with_confirmation:
        category_obj.delete_instance()
        Category.clear_actual_cache()
        Source.clear_actual_cache()
        Filter.clear_actual_cache()

        callback_query.data = '/'
        await callback_query.answer('Категория удалена')
        await set_main_menu(client, callback_query, needs_an_answer=False)

        await send_message_to_admins(
            client,
            callback_query,
            (
                '❌ Удалена категория '
                f'**{await get_channel_formatted_link(category_obj.tg_id)}**'
            ),
        )
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        (
            'Категория: '
            f'**{await get_channel_formatted_link(category_obj.tg_id)}**\n\n'
            'Ты **удаляешь** категорию!'
        ),
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton('❌ Подтвердить удаление', callback_data=f'{path}/')]]
            + buttons.get_footer(path)
        ),
        disable_web_page_preview=True,
    )
