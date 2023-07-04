from pyrogram.enums import MessageEntityType
from pyrogram.raw.types import MessageEntityBold, MessageEntityTextUrl
from pyrogram.types import InputMedia, Message, MessageEntity

from plugins.user.utils import tg_len


class Header:
    def __init__(self, message: Message):
        self._message = message
        self._src_text = f'💬 Источник: {message.chat.title or message.chat.id}'
        self._fwd_text = None
        if message.forward_from_chat:
            self._fwd_text = f'fwd: {message.forward_from_chat.title or message.forward_from_chat.id}'

    @property
    def text(self):
        if self._fwd_text:
            return f'{self._src_text}\n{self._fwd_text}\n\n'
        return f'{self._src_text}\n\n'

    @property
    def entities(self):
        entities = [
            MessageEntity(
                type=MessageEntityType.BOLD,
                offset=0,
                length=tg_len(self._src_text),
            ),
            MessageEntity(
                type=MessageEntityType.TEXT_LINK,
                offset=0,
                length=tg_len(self._src_text),
                url=self._message.link,
            ),
        ]
        if self._fwd_text:
            entities.append(
                MessageEntity(
                    type=MessageEntityType.TEXT_LINK,
                    offset=tg_len(self._src_text) + 1,  # len(src_text) + len('\n')
                    length=tg_len(self._fwd_text),
                    url=(
                        f'https://t.me/{self._message.forward_from_chat.username}'
                        f'/{self._message.forward_from_message_id}'
                    ),
                ),
            )
        return entities

    @property
    def raw_entities(self):
        raw_entities = [
            MessageEntityBold(
                offset=0,
                length=tg_len(self._src_text),
            ),
            MessageEntityTextUrl(
                offset=0,
                length=tg_len(self._src_text),
                url=self._message.link,
            ),
        ]
        if self._fwd_text:
            raw_entities.append(
                MessageEntityTextUrl(
                    offset=tg_len(self._src_text) + 1,  # len(src_text) + len('\n')
                    length=tg_len(self._fwd_text),
                    url=(
                        f'https://t.me/{self._message.forward_from_chat.username}'
                        f'/{self._message.forward_from_message_id}'
                    ),
                ),
            )
        return raw_entities


def add_header(obj: Message | InputMedia, header: Header, is_media: bool) -> None:
    text = header.text
    if is_media:
        for entity in obj.caption_entities or []:
            entity.offset += tg_len(text)

        obj.caption = text + (obj.caption or '')
        if isinstance(obj, InputMedia):
            obj.caption_entities = header.raw_entities + (obj.caption_entities or [])
        else:
            obj.caption_entities = header.entities + (obj.caption_entities or [])
    else:
        for entity in obj.entities or []:
            entity.offset += tg_len(text)

        obj.text = text + (obj.text or '')
        obj.entities = header.entities + (obj.entities or [])
