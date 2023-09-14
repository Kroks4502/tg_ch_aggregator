import itertools
import re

from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.user.utils.text_length import tg_len


def cleanup_message(message: Message, source: Source, is_media: bool) -> None:
    global_cleanup_list = (
        GlobalSettings.select(GlobalSettings.value)
        .where(GlobalSettings.key == "cleanup_list")
        .get()
        .value
    )

    for pattern in itertools.chain(
        global_cleanup_list,
        source.cleanup_list,
    ):
        text = message.caption or message.text
        if not text:
            break

        find_result = re.finditer(
            pattern,
            string=text,
            flags=re.IGNORECASE,
        )
        cut_len = 0
        for match in find_result:
            start = match.start()
            end = match.end()
            cut_len += remove_text(
                message=message,
                start=start - cut_len,
                end=end - cut_len,
                is_media=is_media,
            )


def remove_text(message: Message, start: int, end: int, is_media: bool) -> int:
    separator = "\n\n"
    # message.Str to str
    text = str(message.caption or message.text)
    text = text[:start] + f'{separator if start != 0 else ""}' + text[end:]

    entities_new = []
    cut_len = end - start - (tg_len(separator) if start != 0 else 0)
    for entity in message.entities or message.caption_entities or []:
        # Оставляем только разметку оставшегося текста
        offset = entity.offset
        if offset < start and offset + entity.length <= start + tg_len(separator):
            entities_new.append(entity)
        elif offset >= end:
            # Делаем сдвиг сущностей
            entity.offset -= cut_len
            entities_new.append(entity)

    if is_media:
        message.caption = text
        message.caption_entities = entities_new
    else:
        message.text = text
        message.entities = entities_new

    return cut_len
