import math


class Pagination:
    """Пагинация меню бота."""

    # Параметры для пустой кнопки
    # Используется, чтобы не менялась сетка кнопок
    # при переключении страниц
    EMPTY_BUTTON_PARAMS = ("·", "·")

    def __init__(
        self,
        page: int,
        size: int,
        total_items: int,
    ):
        """
        :param page: Номер текущей страницы.
        :param size: Размер страницы.
        :param total_items: Общее количество элементов.
        """
        self.page = page
        self.size = size
        self.total_items = total_items
        self.last_page = math.ceil(self.total_items / self.size)
        self.offset = (page - 1) * size
        self.offset_with_size = self.offset + size

    def get_pagination_buttons_params(self) -> list[tuple[str, str]]:
        """Получить параметры кнопок пагинации."""
        first_params = self.EMPTY_BUTTON_PARAMS
        prev_params = self.EMPTY_BUTTON_PARAMS
        next_params = self.EMPTY_BUTTON_PARAMS
        last_params = self.EMPTY_BUTTON_PARAMS

        path_tmpl = "p/{}"

        if self.page > 1:
            prev_page = self.page - 1
            prev_params = "⬅️", path_tmpl.format(prev_page)

            if self.page > 2:
                first_params = "⏪", path_tmpl.format(1)

        pages = f"{self.page}/{self.last_page}", "·"

        if self.page < self.last_page:
            next_page = self.page + 1
            next_params = "➡️", path_tmpl.format(next_page)

            if self.page < self.last_page - 1:
                last_params = "⏩", path_tmpl.format(self.last_page)

        return [first_params, prev_params, pages, next_params, last_params]

    def is_exists(self) -> bool:
        """Доступны ли кнопки пагинации или они все пустые."""
        return self.total_items > self.size
