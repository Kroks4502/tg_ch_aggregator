def tg_len(text: str) -> int:
    """Возвращает длину текста, соответствующую Telegram API."""
    return len(text.encode("utf-16-le")) // 2


def tg_slice(text: str, length: int) -> str:
    """
    Обрезает строку до указанной длины в единицах Telegram (UTF-16-LE).

    Аналог pyrogram.types.messages_and_media.message.Str(text)[:length]:
    emoji и суррогатные пары считаются как 2 единицы, обычные символы — как 1.
    """
    encoded = text.encode("utf-16-le")
    return encoded[: length * 2].decode("utf-16-le", errors="ignore")
