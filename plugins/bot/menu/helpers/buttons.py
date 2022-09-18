from typing import Type

from pyrogram.types import InlineKeyboardButton

from models import BaseModel
from plugins.bot.menu.helpers.path import Path


def get_fixed(path: Path, back_title='Назад') -> list[
    list[InlineKeyboardButton]]:
    row_buttons = [InlineKeyboardButton('🗂 На главную', callback_data='/')]
    prev_data = path.get_prev()
    if prev_data != '/':
        row_buttons.append(
            InlineKeyboardButton(
                f'🔙 {back_title}', callback_data=prev_data))
    return [row_buttons]


MAX_LENGTH_BUTTON_TEXT = 17


def get_list_model(
        data: Type[BaseModel] | tuple[str],
        path: Path,
        prefix_path: str = '',
        button_show_all_title: str = '',
        select_kwargs: dict = None,
        count_model: Type[BaseModel] = None,
        count_select_kwargs: dict = None
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
        text = t if (t := str(item)) else '<пусто>'
        if count_model and count_select_kwargs:
            fields = {}
            for key, arg in count_select_kwargs.items():
                if isinstance(arg, str) and arg[0] == '.':
                    if isinstance(data, BaseModel):
                        fields[key] = getattr(data, arg[1:])
                    else:
                        fields[key] = item
                else:
                    fields[key] = arg
            count_entities = count_model.filter(**fields).count()
            if count_entities > 0:
                if len(text) > MAX_LENGTH_BUTTON_TEXT:
                    text = f'{text[:MAX_LENGTH_BUTTON_TEXT]}..'
                text = f'{text} ({count_entities})'
        row_buttons.append(
            InlineKeyboardButton(
                text,
                callback_data=path.add_value(prefix_path, value)
            )
        )
    buttons.append(row_buttons)

    return buttons
