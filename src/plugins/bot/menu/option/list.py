import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'^/o/$') & custom_filters.admin_only,
)
async def options(_, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.edit_text(
        '**Параметры**',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('Администраторы', callback_data='/o/a/'),
                ],
                [
                    InlineKeyboardButton('История фильтра', callback_data='/o/fh/'),
                ],
                [
                    InlineKeyboardButton('История пересылки', callback_data='/o/mh/'),
                ],
                [
                    InlineKeyboardButton('Статистика', callback_data='/o/statistics/'),
                ],
                [
                    InlineKeyboardButton('💾 Логи', callback_data='/o/:get_logs/'),
                ],
                [
                    InlineKeyboardButton(
                        'Проверить пост', callback_data='/o/:check_post/'
                    ),
                ],
            ]
            + buttons.get_footer(Path(callback_query.data))
        ),
    )
