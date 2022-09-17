from typing import Type

from pyrogram.types import InlineKeyboardButton

from models import BaseModel
from plugins.bot.menu.helpers.path import Path


def get_fixed(path: Path, back_title='Назад') -> list[list[InlineKeyboardButton]]:
    row_buttons = [InlineKeyboardButton('🗂 На главную', callback_data='/')]
    prev_data = path.get_prev()
    if prev_data != '/':
        row_buttons.append(
            InlineKeyboardButton(
                f'🔙 {back_title}', callback_data=prev_data))
    return [row_buttons]


def get_list_model(
        data: Type[BaseModel] | tuple[str],
        path: Path,
        prefix_path: str = '',
        button_show_all_title: str = '',
        select_kwargs: dict = None,
        count_model: Type[BaseModel] = None,
        count_args: list = None
) -> list[list[InlineKeyboardButton]]:
    buttons = []
    row_buttons = []

    if button_show_all_title:
        buttons.append([
            InlineKeyboardButton(
                button_show_all_title,
                callback_data=path.add_value(prefix_path, 0)
            )
        ])

    if select_kwargs:
        data = data.filter(**select_kwargs)

    for item in data:
        if len(row_buttons) == 2:
            buttons.append(row_buttons)
            row_buttons = []
        value = item if isinstance(data, tuple) else item.id
        button_text = t if (t := str(item)) else '<пусто>'
        if count_model and count_args:
            fields = {}
            for arg in count_args:
                fields[arg] = getattr(data, arg)
            button_text += f'({count_model.select(fields).count()})'
        row_buttons.append(
            InlineKeyboardButton(
                button_text,
                callback_data=path.add_value(prefix_path, value)
            )
        )
    buttons.append(row_buttons)

    return buttons
