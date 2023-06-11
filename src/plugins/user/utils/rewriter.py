import re
from typing import Match

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from config import PATTERN_WITHOUT_SMILE


def rewrite_message(message: Message) -> None:
    header, header_entities = get_header(message)

    for entity in message.entities or message.caption_entities or []:
        # Делаем сдвиг сущностей на размер заголовка
        entity.offset += len(header)

    if message.media:
        message.caption = header + (message.caption or '')
        message.caption_entities = header_entities + (message.caption_entities or [])
    else:
        message.text = header + (message.text or '')
        message.entities = header_entities + (message.entities or [])


def get_header(message: Message) -> tuple[str, list[MessageEntity]]:
    src_text = get_src_text(message)
    fwd_text = get_fwd_text(message)

    header = src_text + (f'\n{fwd_text}' if fwd_text else '') + '\n\n'
    header_entities = [
        MessageEntity(
            type=MessageEntityType.BOLD,
            offset=0,
            length=len(src_text),
        ),
        MessageEntity(
            type=MessageEntityType.TEXT_LINK,
            offset=0,
            length=len(src_text),
            url=message.link,
        ),
    ]
    if fwd_text:
        header_entities.append(
            MessageEntity(
                type=MessageEntityType.TEXT_LINK,
                offset=len(src_text) + 1,  # len(src_text) + len('\n')
                length=len(fwd_text),
                url=(
                    f'https://t.me/{message.forward_from_chat.username}'
                    f'/{message.forward_from_message_id}'
                ),
            ),
        )
    return header, header_entities


def get_src_text(message: Message) -> str:
    title = re.sub(
        PATTERN_WITHOUT_SMILE,
        '',
        message.chat.title,
    )
    return (
        f'Источник: {title if title else message.chat.id}'  # 💬 len(💬)=1, but tg len=2
    )


def get_fwd_text(message: Message) -> str:
    if message.forward_from_chat:
        title = re.sub(
            PATTERN_WITHOUT_SMILE,
            '',
            message.forward_from_chat.title,
        )
        return f'fwd: {title if title else message.chat.id}'
    return ''


def delete_agent_text_in_message(search_result: Match, message: Message):  # noqa: C901
    separator = '\n\n'
    title = re.sub(
        PATTERN_WITHOUT_SMILE,
        "",
        (
            message.forward_from_chat.title
            if message.forward_from_chat
            else message.chat.title
        ),
    )
    author = f'💬 Источник: {title if title else message.chat.id}\n\n'
    start = search_result.start()
    end = search_result.end()
    if message.text:
        message.text = str(message.text)
        message.text = (
            author
            + message.text[:start]
            + f'{separator if start != 0 else ""}'
            + message.text[end:]
        )
    elif message.caption:
        message.caption = str(message.caption)
        message.caption = (
            author
            + message.caption[:start]
            + f'{separator if start != 0 else ""}'
            + message.caption[end:]
        )

    cut_text_len = search_result.end() - search_result.start() - len(separator)
    for entity in message.entities or message.caption_entities or []:
        if entity.offset > search_result.start():
            entity.offset -= cut_text_len

    add_author_len = len(author)
    for entity in message.entities or message.caption_entities or []:
        entity.offset += add_author_len + 1

    bold = MessageEntity(type=MessageEntityType.BOLD, offset=0, length=add_author_len)
    url = message.link
    if message.forward_from_chat and message.forward_from_chat.username:
        url = (
            f'https://t.me/{message.forward_from_chat.username}/'
            f'{message.forward_from_message_id}'
        )
    text_link = MessageEntity(
        type=MessageEntityType.TEXT_LINK,
        offset=0,
        length=add_author_len - 1,
        url=url,
    )
    if message.text:
        if not message.entities:
            message.entities = []
        message.entities.insert(0, bold)
        message.entities.insert(0, text_link)
    if message.caption:
        if not message.caption_entities:
            message.caption_entities = []
        message.caption_entities.insert(0, bold)
        message.caption_entities.insert(0, text_link)
