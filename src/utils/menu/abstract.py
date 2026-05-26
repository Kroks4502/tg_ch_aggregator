import abc
from typing import Type

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from utils import menu
from utils.menu.pagination import Pagination
from utils.menu.path import Path


class MenuAbstract(abc.ABC):
    """Абстрактный класс для организации меню бота."""

    MAIN_MENU_BUTTON_TITLE = "🏠 На главную"
    BACK_BUTTON_TITLE_TEMPLATE = "🔙 {}"

    PAGINATION_NUMBER_ITEMS_PER_PAGE = 20

    MAX_LENGTH_BUTTON_TEXT = 12

    @property
    @abc.abstractmethod
    def button_adder(self) -> Type["menu.ButtonAdderBase"]:
        return menu.ButtonAdderBase

    def __init__(
        self,
        path: str,
        *,
        back_title: str = "Назад",
        back_step: int = 1,
    ):
        """
        :param path: Текущий путь меню.
        :param back_title: Текст кнопки "Назад".
        :param back_step: Количество шагов для кнопки "Назад".
        """
        self.inline_keyboard = []
        self.after_pagination_buttons_row = []

        self.raw_path = path
        self.path = Path(self.get_path_without_params())

        self.back_title = back_title
        self.back_step = back_step
        self.pagination = None
        self.need_send_new_message = False if self.raw_path.find("?new") == -1 else True

        self.set_footer_buttons = True

    def get_path_without_params(self) -> str:
        """Получить путь без номера страницы и других параметров."""
        pag_idx = self.raw_path.find("p/") or self.raw_path.find("?new")
        if pag_idx != -1:
            return self.raw_path[:pag_idx]

        return self.raw_path

    def set_pagination(
        self,
        total_items: int,
        size: int = None,
    ) -> Pagination:
        """Установить параметры пагинации меню."""
        self.pagination = Pagination(
            page=Path(self.raw_path).get_value("p") or 1,
            size=size or self.PAGINATION_NUMBER_ITEMS_PER_PAGE,
            total_items=total_items,
        )
        return self.pagination

    def add_row_button(self, text: str, path: str, new: bool = False) -> None:
        """
        Добавить строку из одной кнопки.

        :param text: Текст кнопки.
        :param path: Абсолютный или относительный путь.
        :param new: Отправлять новое сообщение.
        """
        self.inline_keyboard.append(
            [
                self._get_inline_keyboard_button(text=text, path=path, new=new),
            ]
        )

    def add_row_button_after_pagination(
        self, text: str, path: str, new: bool = False
    ) -> None:
        """
        Добавить строку из одной кнопки после пагинации.

        :param text: Текст кнопки.
        :param path: Абсолютный или относительный путь.
        :param new: Отправлять новое сообщение.
        """
        self.after_pagination_buttons_row.append(
            [
                self._get_inline_keyboard_button(text=text, path=path, new=new),
            ]
        )

    def _get_inline_keyboard_button(self, text: str, path: str, new: bool = False):
        return InlineKeyboardButton(
            text=text, callback_data=self.path.join(path) + ("?new" if new else "")
        )

    def add_row_many_buttons(self, *buttons_args: tuple[str, str]) -> None:
        """
        Добавить строку из нескольких кнопок.

        :param buttons_args: Кортеж, где первый элемент – текст кнопки, второй – абсолютный или относительный путь.
        """
        self.inline_keyboard.append(
            [
                InlineKeyboardButton(text=b[0], callback_data=self.path.join(b[1]))
                for b in buttons_args
            ]
        )

    def add_rows_from_data(
        self,
        data: list["menu.ButtonData"],
        postfix: str = "",
    ) -> None:
        """
        Добавить строки кнопок для списка элементов из данных.

        :param data: Данные для преобразования в кнопки.
        :param postfix: Постфикс для добавления в конец пути.
        :return: None
        """
        row_buttons = []

        for item in data:
            if len(row_buttons) == 2:
                self.inline_keyboard.append(row_buttons)
                row_buttons = []

            row_buttons.append(
                InlineKeyboardButton(
                    text=item.get_processed_title(length=self.MAX_LENGTH_BUTTON_TEXT),
                    callback_data=self.path.join(item.path) + postfix,
                )
            )
        self.inline_keyboard.append(row_buttons)

    @property
    def add_button(self) -> "menu.ButtonAdderBase":
        return self.button_adder(self)

    @property
    def reply_markup(self):
        pagination_buttons_row = self.get_pagination_buttons_row()
        footer_buttons_row = self.get_footer_buttons_row()
        if not (
            self.inline_keyboard
            or self.after_pagination_buttons_row
            or pagination_buttons_row
            or footer_buttons_row
        ):
            return None

        return InlineKeyboardMarkup(
            inline_keyboard=(
                self.inline_keyboard
                + [pagination_buttons_row]
                + self.after_pagination_buttons_row
                + [footer_buttons_row]
            )
        )

    def get_pagination_buttons_row(self) -> list:
        if not (self.pagination and self.pagination.is_exists()):
            return []

        return [
            InlineKeyboardButton(text=text, callback_data=self.path.join(path))
            for text, path in self.pagination.get_pagination_buttons_params()
        ]

    def get_footer_buttons_row(self) -> list[InlineKeyboardButton]:
        if self.path.is_root() or not self.set_footer_buttons:
            return []

        footer_buttons_row = [
            InlineKeyboardButton(text=self.MAIN_MENU_BUTTON_TITLE, callback_data="/"),
        ]

        prev_path = self.path.get_prev(self.back_step)
        if prev_path != "/":
            footer_buttons_row.append(
                InlineKeyboardButton(
                    text=self.BACK_BUTTON_TITLE_TEMPLATE.format(self.back_title),
                    callback_data=prev_path,
                ),
            )

        return footer_buttons_row

    def __str__(self):
        return str(self.inline_keyboard)
