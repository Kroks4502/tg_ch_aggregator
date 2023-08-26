from dataclasses import dataclass

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from filter_types import FILTER_TYPES_BY_ID
from models import Admin, Category, Filter, Source
from plugins.bot.constants import DEFAULT_NUM_ITEMS_ON_MENU, MAX_LENGTH_BUTTON_TEXT
from plugins.bot.utils.links import get_channel_formatted_link, get_user_formatted_link
from plugins.bot.utils.pagination import Pagination
from plugins.bot.utils.path import Path


class Menu:
    """Меню бота."""

    def __init__(
        self,
        path: str,
        *,
        back_title: str = 'Назад',
        back_step: int = 1,
    ):
        """
        :param path: Текущий путь меню.
        :param back_title: Текст кнопки "Назад".
        :param back_step: Количество шагов для кнопки "Назад".
        """
        self.inline_keyboard = []

        self.raw_path = path
        self.path = Path(self.get_path_without_pagination())

        self.back_title = back_title
        self.back_step = back_step
        self.pagination = None

    def get_path_without_pagination(self) -> str:
        """Получить путь без номера страницы."""
        pag_idx = self.raw_path.find('p/')
        if pag_idx == -1:
            return self.raw_path
        return self.raw_path[:pag_idx]

    def set_pagination(
        self,
        total_items: int,
        size: int = DEFAULT_NUM_ITEMS_ON_MENU,
    ) -> Pagination:
        """Установить параметры пагинации меню."""
        self.pagination = Pagination(
            page=Path(self.raw_path).get_value('p') or 1,
            size=size,
            total_items=total_items,
        )
        return self.pagination

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
    ) -> str:
        if filter_obj:
            source_obj = filter_obj.source
            filter_type_id = filter_obj.type

        if source_obj:
            category_obj = source_obj.category

        breadcrumbs = []

        if category_obj:
            link = await get_channel_formatted_link(category_obj.id)
            breadcrumbs.append(f'Категория: **{link}**')

        if source_obj:
            link = await get_channel_formatted_link(source_obj.id)
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
            link = await get_user_formatted_link(admin_obj.id)
            breadcrumbs.append(f'**{link}**')

        pagination_text = ''
        if self.pagination and self.pagination.is_exists():
            pagination_text = (
                f'Страница {self.pagination.page} из {self.pagination.last_page}'
            )

        result_text_items = [
            item
            for item in (
                start_text,
                '\n'.join(breadcrumbs),
                last_text,
                pagination_text,
            )
            if item
        ]

        return '\n\n'.join(result_text_items) or '<пусто>'

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
        pagination_buttons_row = self.get_pagination_buttons_row()
        footer_buttons_row = self.get_footer_buttons_row()
        if not (self.inline_keyboard or pagination_buttons_row or footer_buttons_row):
            return None

        return InlineKeyboardMarkup(
            self.inline_keyboard + [pagination_buttons_row] + [footer_buttons_row]
        )

    def get_pagination_buttons_row(self) -> list:
        if not (self.pagination and self.pagination.is_exists()):
            return []

        return [
            InlineKeyboardButton(text=text, callback_data=self.path.join(path))
            for text, path in self.pagination.get_pagination_buttons_params()
        ]

    def get_footer_buttons_row(self) -> list[InlineKeyboardButton]:
        if self.path.is_root():
            return []

        footer_buttons_row = [
            InlineKeyboardButton('🏠 На главную', callback_data='/'),
        ]

        prev_path = self.path.get_prev(self.back_step)
        if prev_path != '/':
            footer_buttons_row.append(
                InlineKeyboardButton(f'🔙 {self.back_title}', callback_data=prev_path),
            )

        return footer_buttons_row

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
