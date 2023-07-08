def tg_len(text: str) -> int:
    """Возвращает длину текста, соответствующую Telegram API."""
    return len(text.encode('utf-16-le')) // 2
