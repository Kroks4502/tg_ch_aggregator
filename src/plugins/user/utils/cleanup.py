import itertools
import re

from pyrogram.types import Message

from models import GlobalSettings, Source


def cleanup_message(message: Message, source: Source) -> None:
    if not (message.caption or message.text):
        return
    global_cleanup_regex = next(GlobalSettings.get_cache(key='cleanup_regex'))['value']

    for pattern in itertools.chain(
        global_cleanup_regex,
        source.cleanup_regex,
    ):
        find_result = re.finditer(pattern, message.caption or message.text)
        cut_len = 0
        for match in find_result:
            start = match.start()
            end = match.end()
            cut_len += remove_text(
                message=message,
                start=start - cut_len,
                end=end - cut_len,
            )


def remove_text(message: Message, start: int, end: int) -> int:
    separator = '\n\n'
    text = message.caption if message.media else message.text
    text = text[:start] + f'{separator if start != 0 else ""}' + text[end:]

    entities_new = []
    cut_len = end - start - (len(separator) if start != 0 else 0)
    for entity in message.entities or message.caption_entities or []:
        # Оставляем только разметку оставшегося текста
        offset = entity.offset
        if offset < start and offset + entity.length <= start:
            entities_new.append(entity)
        elif offset >= end:
            # Делаем сдвиг сущностей
            entity.offset -= cut_len
            entities_new.append(entity)

    if message.media:
        message.caption = text
        message.caption_entities = entities_new
    else:
        message.text = text
        message.entities = entities_new

    return cut_len
