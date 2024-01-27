import itertools
import re

from pyrogram.types import Message

from models import GlobalSettings, Source
from plugins.user.utils.text_length import tg_len

TEXT_SEPARATOR = "\n\n"
STRIP_CHARS = " \n"


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
        offset = 0
        for match in find_result:
            start = match.start()
            end = match.end()

            text, entities, next_offset = remove_text(
                text=str(message.caption or message.text),  # message.Str to str
                entities=message.caption_entities or message.entities or (),
                start=start - offset,
                end=end - offset,
            )
            offset += next_offset

            if is_media:
                message.caption = text
                message.caption_entities = entities
            else:
                message.text = text
                message.entities = entities


def remove_text(
    text: str,
    entities: list,
    start: int,
    end: int,
) -> tuple[str, list, int]:
    text_before_start = text[:start]
    text_after_end = text[end:]

    if cut_length := tg_len(text) - tg_len(text_before_start) - tg_len(text_after_end):
        entities = cut_entities(
            entities=entities,
            offset=tg_len(text_before_start),
            length=cut_length,
        )

    text_before_start, tbs_strip_len_l = left_strip(text_before_start)
    if tbs_strip_len_l:
        entities = cut_entities(
            entities=entities,
            offset=0,
            length=tbs_strip_len_l,
        )

    text_before_start, tbs_strip_len_r = right_strip(text_before_start)
    if tbs_strip_len_r:
        entities = cut_entities(
            entities=entities,
            offset=tg_len(text_before_start),
            length=tbs_strip_len_r,
        )

    text_after_end, tae_strip_len_l = left_strip(text_after_end)
    if tae_strip_len_l:
        entities = cut_entities(
            entities=entities,
            offset=tg_len(text_before_start),
            length=tae_strip_len_l,
        )

    text_after_end, tae_strip_len_r = right_strip(text_after_end)
    if tae_strip_len_r:
        entities = cut_entities(
            entities=entities,
            offset=tg_len(text_before_start) + tg_len(text_after_end),
            length=tae_strip_len_r,
        )

    next_offset = end - start + tbs_strip_len_l + tbs_strip_len_r + tae_strip_len_l
    if text_before_start and text_after_end:
        text = f"{text_before_start}{TEXT_SEPARATOR}{text_after_end}"
        next_offset -= tg_len(TEXT_SEPARATOR)
        entities = push_entities(
            entities=entities,
            offset=tg_len(text_before_start),
            length=tg_len(TEXT_SEPARATOR),
            text_length=tg_len(text),
        )
    else:
        text = text_before_start or text_after_end

    return text, entities, next_offset


def left_strip(text: str) -> tuple[str, int]:
    res = text.lstrip(STRIP_CHARS)
    return res, tg_len(text) - tg_len(res)


def right_strip(text: str) -> tuple[str, int]:
    res = text.rstrip(STRIP_CHARS)
    return res, tg_len(text) - tg_len(res)


def cut_entities(entities: list, offset: int, length: int):
    entities_new = []
    end = offset + length

    for entity in entities:
        if entity.offset < offset:
            if entity.offset + entity.length > offset:
                if entity.offset + entity.length > end:
                    entity.length -= length
                else:
                    entity.length = offset - entity.offset
        elif entity.offset + entity.length > end:
            if entity.offset < end:
                shift = end - entity.offset
                entity.offset -= length - shift
                entity.length -= shift
            else:
                entity.offset -= length
        else:
            continue

        entities_new.append(entity)

    return entities_new


def push_entities(entities: list, offset: int, length: int, text_length: int):
    max_length = text_length + length

    for entity in entities:
        if entity.offset >= offset:
            entity.offset += length
        elif entity.offset + entity.length > offset:
            entity.length += length

        if entity.offset + entity.length > max_length:
            entity.length = max_length - entity.offset

    return entities
