from pyrogram.types import InlineKeyboardButton

from plugins.bot.utils.path import Path


def get_footer(
    path: Path,
    back_title: str = 'Назад',
) -> list[
    list[InlineKeyboardButton]
]:  # todo должно быть удалено после внедрения utils.inline_keyboard.Menu
    """
    Получить фиксированные кнопки "Главная" и "Назад".

    :param path: Текущий путь в меню.
    :param back_title: Текст кнопки "Назад".
    :return: Фиксированные кнопки.
    """
    row_buttons = [
        InlineKeyboardButton(
            '🗂 На главную',
            callback_data='/',
        )
    ]
    prev_data = path.get_prev()
    if prev_data != '/':
        row_buttons.append(
            InlineKeyboardButton(
                f'🔙 {back_title}',
                callback_data=prev_data,
            )
        )
    return [row_buttons]


MAX_LENGTH_BUTTON_TEXT = 12


def get_list(
    data: dict[int | str, tuple[str | None, int]], path: Path, postfix: str = ''
) -> list[list[InlineKeyboardButton]]:
    """
    Получить кнопки для списка данных.

    :param data: Данные для преобразования в кнопки. Ключ - id, значение кортеж из имени кнопки и количества сущностей.
    :param path: Текущий путь в меню.
    :param postfix: Постфикс для формирования пути.
    :return: Кнопки из данных.
    """
    buttons = []
    row_buttons = []

    for key, (title, amount) in data.items():
        if len(row_buttons) == 2:
            buttons.append(row_buttons)
            row_buttons = []

        title = title if title else '<пусто>'
        if amount:
            if len(title) > MAX_LENGTH_BUTTON_TEXT:
                title = f'{title[:MAX_LENGTH_BUTTON_TEXT]}'
                title = title[:-1] if title[-1] == ' ' else title
                title += '…'
            title = f'{title} ({amount})'

        row_buttons.append(
            InlineKeyboardButton(
                title,
                callback_data=path.add_value(key) + postfix,
            )
        )
    buttons.append(row_buttons)

    return buttons
