import itertools
import re

from pyrogram.types import Message

from models import GlobalSettings, Source

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
            offset += remove_text(
                message=message,
                start=start - offset,
                end=end - offset,
                is_media=is_media,
            )


def remove_text(  # noqa: C901
    message: Message,
    start: int,
    end: int,
    is_media: bool,
) -> int:
    # message.Str to str
    text = str(message.caption or message.text)
    entities = message.caption_entities or message.entities or ()

    fin_offset = end - start

    text_before_start = text[:start]

    text_before_start, text_before_start_cut_len_l = left_strip(text_before_start)
    fin_offset += text_before_start_cut_len_l

    text_before_start, text_before_start_cut_len_r = right_strip(text_before_start)
    fin_offset += text_before_start_cut_len_r

    text_after_end = text[end:]

    text_after_end, text_after_end_cut_len_l = left_strip(text_after_end)
    fin_offset += text_after_end_cut_len_l

    text_after_end, _ = right_strip(text_after_end)

    if text_before_start and text_after_end:
        text = f"{text_before_start}{TEXT_SEPARATOR}{text_after_end}"
        fin_offset -= len(TEXT_SEPARATOR)
    else:
        text = text_before_start or text_after_end

    entities_new = []
    for entity in entities:
        if entity.offset < start - text_before_start_cut_len_r:
            end_entity_idx = entity.offset + entity.length
            if start <= end_entity_idx < end:
                entity.length = (
                    text_before_start_cut_len_l + len(text_before_start) - entity.offset
                )
            elif end_entity_idx > end:
                entity.length -= (
                    text_before_start_cut_len_r
                    + end
                    - start
                    + text_after_end_cut_len_l
                    - (
                        len(TEXT_SEPARATOR)
                        if text_before_start and text_after_end
                        else 0
                    )
                )
            elif end_entity_idx == end:
                entity.length -= text_before_start_cut_len_r + end - start
            entities_new.append(entity)
        elif entity.offset + entity.length > end + text_after_end_cut_len_l:
            entity.offset -= fin_offset

            if entity.offset < 0:
                entity.length -= (
                    end - start + text_before_start_cut_len_r + text_after_end_cut_len_l
                )
                entity.offset = 0
            elif entity.offset + entity.length > len(text):
                entity.length = len(text) - entity.offset
            entities_new.append(entity)

    if is_media:
        message.caption = text
        message.caption_entities = entities_new
    else:
        message.text = text
        message.entities = entities_new

    return fin_offset


def left_strip(text: str) -> tuple[str, int]:
    res = text.lstrip(STRIP_CHARS)
    return res, len(text) - len(res)


def right_strip(text: str) -> tuple[str, int]:
    res = text.rstrip(STRIP_CHARS)
    return res, len(text) - len(res)
