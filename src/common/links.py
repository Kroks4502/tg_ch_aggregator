from pyrogram import utils


def get_message_link(chat_id: int, message_id: int):
    """
    Сформировать ссылку на сообщение в канале.

    :param chat_id: ID чата.
    :param message_id: ID сообщения.
    :return: Ссылка на сообщение.
    """
    return f"https://t.me/c/{utils.get_channel_id(chat_id)}/{message_id}"
