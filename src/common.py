from pyrogram import utils


def get_message_link(chat_id: int, message_id: int):
    """
    Сформировать ссылку на сообщение в канале.

    :param chat_id: ID чата.
    :param message_id: ID сообщения.
    :return: Ссылка на сообщение.
    """
    return f"https://t.me/c/{utils.get_channel_id(chat_id)}/{message_id}"


def get_shortened_text(text: str, max_len: int, *, last_trim_char: str = "…") -> str:
    """
    Получить сокращенный текст.

    :param text: Исходный текст.
    :param max_len: Максимальная длина сокращенного текста.
    :param last_trim_char: Последний символ, добавляемый в возвращаемую строку.
    :return: Сокращенный текст.
    """
    if len(text) <= max_len:
        return text

    new_text = ""
    for item in text.split(" "):
        if len(new_text + item) > max_len:
            break
        new_text += f"{item} "

    if new_text:
        return f"{new_text[:-1]}{last_trim_char}"
    return f"{text[:max_len]}{last_trim_char}"


def get_words(text: str, line: int = None) -> list:
    if line is None:
        return [word for word in text.split(" ") if word != ""]

    if (lines := text.splitlines()) and len(lines) > line and (line := lines[line]):
        return [word for word in line.split(" ") if word != ""]

    return []
