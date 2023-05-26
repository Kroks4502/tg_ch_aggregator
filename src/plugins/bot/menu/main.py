import logging

import peewee
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from models import Category, Source
from plugins.bot.utils import buttons

from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.path import Path


def main_menu(data: Message | CallbackQuery) -> (str, list[list]):
    path = Path('/')

    text = '**Агрегатор каналов**'

    inline_keyboard = []
    if is_admin(data.from_user.id):
        inline_keyboard.append(
            [
                InlineKeyboardButton(
                    '➕',
                    callback_data=path.add_action('add'),
                ),
                InlineKeyboardButton(
                    '⚙',
                    callback_data='/o/',
                ),
            ]
        )
    inline_keyboard += list_category_buttons(path, f'📚 Все источники')
    inline_keyboard.append(
        [
            InlineKeyboardButton(
                f'🔘 Общие фильтры',
                callback_data=path.add_value('s', 0),
            )
        ]
    )

    return text, inline_keyboard


@Client.on_callback_query(
    filters.regex(r'^/$'),
)
async def set_main_menu(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    text, inline_keyboard = main_menu(callback_query)
    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
    )


def list_category_buttons(path: Path, button_show_all_title='') -> list[list]:
    query = (
        Category.select(
            Category.id,
            Category.title,
            peewee.fn.Count(Source.id).alias('count'),
        )
        .join(Source, peewee.JOIN.LEFT_OUTER)
        .group_by(Category.id)
    )
    return buttons.get_list(
        data={f'{item.id}': (item.title, item.count) for item in query},
        path=path,
        prefix_path='c',
        button_show_all_title=button_show_all_title,
    )
