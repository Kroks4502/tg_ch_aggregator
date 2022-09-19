from typing import Type

from pyrogram.types import InlineKeyboardButton

from models import BaseModel
from plugins.bot.menu.helpers.path import Path


def get_fixed(
        path: Path, back_title='Назад') -> list[list[InlineKeyboardButton]]:
    row_buttons = [InlineKeyboardButton('🗂 На главную', callback_data='/')]
    prev_data = path.get_prev()
    if prev_data != '/':
        row_buttons.append(
            InlineKeyboardButton(
                f'🔙 {back_title}', callback_data=prev_data))
    return [row_buttons]


MAX_LENGTH_BUTTON_TEXT = 16


def get_list_model(
        data: Type[BaseModel] | tuple[str],
        path: Path,
        prefix_path: str = '',
        button_show_all_title: str = '',
        filter_kwargs: dict = None,
        counter_model: Type[BaseModel] = None,
        counter_filter_field_item: str = '',
        counter_filter_fields: dict = None,
        counter_filter_fields_with_data_attr: dict = None,
) -> list[list[InlineKeyboardButton]]:
    if counter_filter_fields is None:
        counter_filter_fields = {}
    if counter_filter_fields_with_data_attr is None:
        counter_filter_fields_with_data_attr = {}

    buttons = []
    row_buttons = []

    if filter_kwargs:
        data = data.filter(**filter_kwargs)

    for item in data:
        if len(row_buttons) == 2:
            buttons.append(row_buttons)
            row_buttons = []

        text = t if (t := str(item)) else '<пусто>'
        if counter_model:
            fields = {}
            for key, attr in counter_filter_fields_with_data_attr.items():
                fields[key] = getattr(item, attr)
            for key, value in counter_filter_fields.items():
                fields[key] = value
            if counter_filter_field_item:
                fields[counter_filter_field_item] = item
            count_entities = counter_model.filter(**fields).count()
            if count_entities:
                if len(text) > MAX_LENGTH_BUTTON_TEXT:
                    text = f'{text[:MAX_LENGTH_BUTTON_TEXT]}'
                    text = text[:-1] if text[-1] == ' ' else text
                    text += '…'
                text = f'{text} ({count_entities})'

        callback_data_value = item if isinstance(data, tuple) else item.id
        row_buttons.append(
            InlineKeyboardButton(
                text,
                callback_data=path.add_value(prefix_path, callback_data_value)
            )
        )
    buttons.append(row_buttons)

    if button_show_all_title:
        buttons.append([
            InlineKeyboardButton(
                button_show_all_title,
                callback_data=path.add_value(prefix_path, 0)
            )
        ])

    return buttons
