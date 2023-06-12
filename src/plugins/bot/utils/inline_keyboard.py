from dataclasses import dataclass

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from filter_types import FILTER_TYPES_BY_ID
from models import Admin, Category, Filter, Source
from plugins.bot.constants import MAX_LENGTH_BUTTON_TEXT
from plugins.bot.utils.links import get_channel_formatted_link, get_user_formatted_link
from plugins.bot.utils.path import Path


class Menu:
    path: Path

    def __init__(self, path: str, *, back_title: str = 'Назад', back_step: int = 1):
        self.inline_keyboard = []

        self.path = Path(path)

        if path == '/':
            self.footer_buttons_row = None
            return

        self.footer_buttons_row = [
            InlineKeyboardButton('🗂 На главную', callback_data='/')
        ]
        prev_path = self.path.get_prev(back_step)
        if prev_path != '/':
            self.footer_buttons_row.append(
                InlineKeyboardButton(f'🔙 {back_title}', callback_data=prev_path)
            )

    async def get_text(  # noqa: C901
        self,
        *,
        category_obj: Category = None,
        source_obj: Source = None,
        filter_obj: Filter = None,
        filter_type_id: str = None,
        cleanup_pattern: str = None,
        admin_obj: Admin = None,
        start_text: str = None,
        last_text: str = None,
    ):
        if filter_obj:
            source_obj = filter_obj.source
            filter_type_id = filter_obj.type

        if source_obj:
            category_obj = source_obj.category

        breadcrumbs = []

        if category_obj:
            link = await get_channel_formatted_link(category_obj.tg_id)
            breadcrumbs.append(f'Категория: **{link}**')

        if source_obj:
            link = await get_channel_formatted_link(source_obj.tg_id)
            breadcrumbs.append(f'Источник: **{link}**')

        if filter_type_id:
            if not source_obj:
                breadcrumbs.append('**Общие фильтры**')
            filter_type_text = FILTER_TYPES_BY_ID.get(filter_type_id)
            breadcrumbs.append(f'Тип фильтра: **{filter_type_text}**')

        if filter_obj:
            breadcrumbs.append(f'Паттерн: `{filter_obj.pattern}`')

        if cleanup_pattern:
            if not source_obj:
                breadcrumbs.append('**Общая очистка текста**')
            breadcrumbs.append(f'Паттерн очистки текста: `{cleanup_pattern}`')

        if admin_obj:
            link = await get_user_formatted_link(admin_obj.tg_id)
            breadcrumbs.append(f'**{link}**')

        text = ''
        if start_text:
            text += start_text

        if breadcrumbs:
            text += '\n\n' + '\n'.join(breadcrumbs)

        if last_text:
            text += f'\n\n{last_text}'

        if text:
            return text.strip('\n')

        return '<пусто>'

    def add_row_button(self, text: str, path: str) -> None:
        """
        Добавить строку из одной кнопки.

        :param text: Текст кнопки.
        :param path: Абсолютный или относительный путь.
        """
        self.inline_keyboard.append(
            [
                InlineKeyboardButton(text=text, callback_data=self.path.join(path)),
            ]
        )

    def add_row_many_buttons(self, *buttons_args: tuple[str, str]) -> None:
        """
        Добавить строку из нескольких кнопок.

        :param buttons_args: Кортеж, где первый элемент – текст кнопки, второй – абсолютный или относительный путь.
        """
        self.inline_keyboard.append(
            [InlineKeyboardButton(b[0], self.path.join(b[1])) for b in buttons_args]
        )

    def add_rows_from_data(
        self,
        data: list['ButtonData'],
        postfix: str = '',
    ) -> None:
        """
        Добавить строки кнопок для списка элементов из данных.

        :param data: Данные для преобразования в кнопки.
        :param postfix: Постфикс для добавления в конец пути.
        :return: Кнопки из данных.
        """
        row_buttons = []

        for item in data:
            if len(row_buttons) == 2:
                self.inline_keyboard.append(row_buttons)
                row_buttons = []

            row_buttons.append(
                InlineKeyboardButton(
                    item.text,
                    callback_data=self.path.join(item.path) + postfix,
                )
            )
        self.inline_keyboard.append(row_buttons)

    @property
    def reply_markup(self):
        if self.footer_buttons_row:
            return InlineKeyboardMarkup(
                self.inline_keyboard + [self.footer_buttons_row]
            )

        if len(self.inline_keyboard) == 0:
            return None

        return InlineKeyboardMarkup(self.inline_keyboard)

    def __str__(self):
        return str(self.inline_keyboard)


@dataclass
class ButtonData:
    """
    - title: Название кнопки (обязательно).
    - path: Относительный путь до объекта (обязательно).
    - amount: Количество объектов.
    """

    title: str
    path: str | int
    amount: str | int = None

    def __post_init__(self):
        self.path = str(self.path)

    @property
    def text(self):
        if len(self.title) > MAX_LENGTH_BUTTON_TEXT:
            self.title = self.title[:MAX_LENGTH_BUTTON_TEXT].rstrip(' ') + '…'

        if self.amount:
            self.title = f'{self.title} ({self.amount})'

        return self.title
