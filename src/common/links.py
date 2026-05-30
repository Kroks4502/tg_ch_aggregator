def get_message_link(chat_id: int, message_id: int) -> str:
    """
    Сформировать ссылку на сообщение в закрытом канале/супергруппе.

    :param chat_id: Помеченный chat_id в формате -100XXXXXXXXXX.
    :param message_id: ID сообщения.
    :return: Ссылка вида https://t.me/c/{bare_channel_id}/{message_id}.
    """
    # Преобразуем -100XXXXXXXXXX → XXXXXXXXXX
    bare_channel_id = -(chat_id + 10 ** 12)
    return f"https://t.me/c/{bare_channel_id}/{message_id}"
