import json
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Union

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from plugins.user.utils.text_length import tg_len


class TextItem:
    def __init__(self, text: str, url: str = None, bold: bool = False):
        self.text = text
        self.entities = []
        self.offset = 0

        if url:
            self.set_link(url=url)

        if bold:
            self.set_bold()

    def set_link(self, url: str):
        self.entities.append(
            MessageEntity(
                type=MessageEntityType.TEXT_LINK,
                offset=self.offset,
                length=len(self),
                url=url,
            )
        )

    def set_bold(self):
        self.entities.append(
            MessageEntity(
                type=MessageEntityType.BOLD,
                offset=self.offset,
                length=len(self),
            )
        )

    def join(self, separator: str, *text_items: "TextItem") -> None:
        shift_offset = 0
        for item in text_items:
            shift_offset += len(self) + tg_len(separator)
            self.text = f"{self.text}{separator}{item.text}"
            for entity in item.entities:
                entity = deepcopy(entity)
                entity.offset += shift_offset
                self.entities.append(entity)

    def shift_entities(self, length: int):
        for entity in self.entities:
            entity.offset += length

    def __str__(self):
        return self.text

    def __repr__(self):
        return json.dumps(
            dict(
                text=self.text,
                entities=list(
                    {
                        str(attr): str(getattr(entity, attr))
                        for attr in filter(
                            lambda x: not x.startswith("_"), entity.__dict__
                        )
                        if getattr(entity, attr) is not None
                    }
                    for entity in self.entities
                ),
            ),
            indent=4,
        )

    def __add__(self, other: Union[str, "TextItem"]) -> "TextItem":
        return deepcopy(self).__iadd__(other)

    def __iadd__(self, other: Union[str, "TextItem"]) -> "TextItem":
        if isinstance(other, str):
            self.text += other
        else:
            shift_offset = len(self)
            self.text += other.text
            for entity in other.entities:
                entity = deepcopy(entity)
                entity.offset += shift_offset
                self.entities.append(entity)
        return self

    def __len__(self):
        return tg_len(self.text)


class AbstractItemController(ABC):
    _additional_item: TextItem

    @property
    @abstractmethod
    def _message(self) -> Message:
        pass

    @property
    @abstractmethod
    def _text_attr_name(self) -> str:
        pass

    @property
    @abstractmethod
    def _entities_attr_name(self) -> str:
        pass

    @abstractmethod
    def include_to_message(self, message: Message, **kwargs) -> None:
        pass

    def __init__(self, item_separator: str = ""):
        self._separator = item_separator
        self._items = []

    def add_item(self, text: str, url: str = None, bold: bool = False) -> None:
        self._items.append(TextItem(text=text, url=url, bold=bold))

    def _join_items(self, end_text: str = "") -> None:
        if len(self._items) == 0:
            self._additional_item = TextItem("") + end_text
            return

        if len(self._items) == 1:
            self._additional_item = self._items[0] + end_text
            return

        self._items[0].join(self._separator, *self._items[1:])
        self._additional_item = self._items[0] + end_text

    def _set_text(self, text: str) -> None:
        setattr(self._message, self._text_attr_name, text)

    def _get_text(self) -> str:
        return getattr(self._message, self._text_attr_name) or ""

    def _set_entities(self, entities: list[MessageEntity]) -> None:
        setattr(self._message, self._entities_attr_name, entities)

    def _get_entities(self) -> list[MessageEntity]:
        return getattr(self._message, self._entities_attr_name) or []
