import itertools
import logging
import re
from typing import Iterable

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from filter_types import FilterMessageType, FilterType
from models import Filter


class FilterInspector:
    def __init__(self, message: Message, source_id: int):
        self._message = message
        self._text = message.text or message.caption
        self._source_id = source_id

    def check_message_type(self) -> dict | None:
        for data in self._get_filters(FilterType.MESSAGE_TYPE):
            try:
                if getattr(
                    self._message, getattr(FilterMessageType, data['pattern']).value[1]
                ):
                    return data
            except AttributeError as e:
                logging.error(e, exc_info=True)

    def check_white_text(self) -> dict | None:
        for data in self._get_filters(FilterType.ONLY_WHITE_TEXT):
            if not self._search(data['pattern'], self._text):
                return data
        return  # noqa: R502

    def check_text(self) -> dict | None:
        for data in self._get_filters(FilterType.TEXT):
            if self._search(data['pattern'], self._text):
                return data
        return  # noqa: R502

    def check_entities(self, entity: MessageEntity) -> dict | None:
        if result := self._check_entity_type(entity):
            return result

        if entity.type == MessageEntityType.HASHTAG:
            return self._check_hashtag(entity)
        if entity.type == MessageEntityType.TEXT_LINK:
            return self._check_text_link(entity)
        if entity.type == MessageEntityType.URL:
            return self._check_url(entity)
        return  # noqa: R502

    def _check_entity_type(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.ENTITY_TYPE):
            try:
                if entity.type == getattr(MessageEntityType, data['pattern'].upper()):
                    return data
            except AttributeError as e:
                logging.error(e, exc_info=True)
        return  # noqa: R502

    def _check_hashtag(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.HASHTAG):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data
        return  # noqa: R502

    def _check_text_link(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(data['pattern'], entity.url):
                return data
        return  # noqa: R502

    def _check_url(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data
        return  # noqa: R502

    def _get_filters(self, f_type: FilterType) -> Iterable[dict]:
        return itertools.chain(
            Filter.get_cache(source=self._source_id, type=f_type.value),
            Filter.get_cache(source=None, type=f_type.value),
        )

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(pattern, string, flags=re.IGNORECASE)
