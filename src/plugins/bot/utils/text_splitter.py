from __future__ import annotations

from typing import List

import settings
from plugins.user.utils.text_length import tg_len


def _split_long_text(text: str, limit: int) -> List[str]:
    """Split long text into chunks that fit within Telegram limits."""
    segments: List[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = line if not current else f"{current}\n{line}"
        if tg_len(candidate) <= limit:
            current = candidate
            continue
        if current:
            segments.append(current)
        if tg_len(line) <= limit:
            current = line
            continue
        chunk = ""
        for char in line:
            candidate = chunk + char
            if tg_len(candidate) <= limit:
                chunk = candidate
            else:
                segments.append(chunk)
                chunk = char
        current = chunk
    if current:
        segments.append(current)
    return segments


def split_markdown(text: str) -> List[str]:
    """Split markdown text into Telegram sized pages preserving paragraphs."""
    if not text:
        return []
    limit = settings.TELEGRAM_MAX_TEXT_LENGTH
    pages: List[str] = []
    page = ""
    for paragraph in text.split("\n\n"):
        if tg_len(paragraph) > limit:
            if page:
                pages.append(page)
                page = ""
            pages.extend(_split_long_text(paragraph, limit))
            continue
        candidate = paragraph if not page else f"{page}\n\n{paragraph}"
        if tg_len(candidate) <= limit:
            page = candidate
        else:
            if page:
                pages.append(page)
            page = paragraph
    if page:
        pages.append(page)
    return pages
