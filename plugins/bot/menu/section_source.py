from pyrogram import Client, filters

from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton)

from initialization import logger
from models import Source
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.section_filter import list_channel

SECTION = '^/s'


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*/s_\d+/$'))
async def detail(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id)

    inline_keyboard = (
            [
                [InlineKeyboardButton(
                    f'Категория: {source_obj.category.title}',
                    callback_data=path.add_action('edit_c')
                ), ],
                [InlineKeyboardButton(
                    '✖️ Удалить источник',
                    callback_data=path.add_action('delete')
                ), ],
            ]
            + buttons.get_fixed(path)
    )

    await callback_query.message.edit_text(
        f'Источник: {source_obj.title}\n\n'
        f'{path}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard)
    )


@Client.on_callback_query(filters.regex(
    SECTION + r'/[\w/]*:edit_c/c_\d+/$'))
async def edit_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id)

    category_id = int(path.get_value('c', after_action=True))

    source_obj.category = category_id
    source_obj.save()

    callback_query.data = path.get_prev(2)
    await detail(_, callback_query)


@Client.on_callback_query(filters.regex(SECTION + r'[\w/]*:delete/'))
async def delete(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    source_id = int(path.get_value('s'))
    source_obj: Source = Source.get(id=source_id)

    if path.with_confirmation:
        callback_query.data = path.get_prev(3)
        source_obj.delete_instance()
        await list_channel(_, callback_query)
        return
    await callback_query.message.edit_text(
        f'Источник: {source_obj.title}\n\n'
        f'{path}',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        '❌ Подтвердить удаление',
                        callback_data=f'{path}/'
                    ),
                ],
            ]
            + buttons.get_fixed(path))
    )
