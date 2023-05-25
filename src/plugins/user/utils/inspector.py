import itertools
import logging
import re

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from filter_types import FilterMessageType, FilterType
from models import CategoryMessageHistory, Filter, Source


def perform_check_history(
    message: Message,
    source: Source,
) -> CategoryMessageHistory | None:
    if message.forward_from_chat:
        forward_source = Source.get_or_none(tg_id=message.forward_from_chat.id)
        if forward_source:
            if h_obj := CategoryMessageHistory.get_or_none(
                category=source.category,
                source=forward_source,
                source_message_id=message.forward_from_message_id,
                deleted=False,
            ):
                return h_obj

        if h_obj := CategoryMessageHistory.get_or_none(
            category=source.category,
            forward_from_chat_id=message.forward_from_chat.id,
            forward_from_message_id=message.forward_from_message_id,
            deleted=False,
        ):
            return h_obj

    else:
        if h_obj := CategoryMessageHistory.get_or_none(
            category=source.category,
            source=source,
            source_message_id=message.id,
            deleted=False,
        ):
            return h_obj

        if h_obj := CategoryMessageHistory.get_or_none(
            category=source.category,
            forward_from_chat_id=message.chat.id,
            forward_from_message_id=message.id,
            deleted=False,
        ):
            return h_obj


def perform_filtering(message: Message, source: Source) -> dict | None:
    inspector = Inspector(message, source)

    if result := inspector.check_message_type():
        return result

    if message.text or message.caption:
        if result := inspector.check_white_text():
            return result
        if result := inspector.check_text():
            return result

    entities = message.entities or message.caption_entities
    if entities:
        for entity in entities:
            if result := inspector.check_entities(entity):
                return result

    return


class Inspector:
    def __init__(self, message: Message, source: Source):
        self._message = message
        self._text = message.text or message.caption
        self._source = source

    def check_message_type(self) -> int | None:
        for data in self._get_filters(FilterType.MESSAGE_TYPE):
            try:
                if getattr(
                    self._message, getattr(FilterMessageType, data['pattern']).value[1]
                ):
                    return data
            except AttributeError as e:
                logging.error(e, exc_info=True)

    def check_white_text(self) -> int | None:
        for data in self._get_filters(FilterType.ONLY_WHITE_TEXT):
            if not self._search(data['pattern'], self._text):
                return data

    def check_text(self) -> int | None:
        for data in self._get_filters(FilterType.TEXT):
            if self._search(data['pattern'], self._text):
                return data

    def check_entities(self, entity: MessageEntity) -> int | None:
        if result := self._check_entity_type(entity):
            return result

        if entity.type == MessageEntityType.HASHTAG:
            return self._check_hashtag(entity)
        elif entity.type == MessageEntityType.TEXT_LINK:
            return self._check_text_link(entity)
        elif entity.type == MessageEntityType.URL:
            return self._check_url(entity)

    def _check_entity_type(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.ENTITY_TYPE):
            try:
                if entity.type == getattr(MessageEntityType, data['pattern'].upper()):
                    return data
            except AttributeError as e:
                logging.error(e, exc_info=True)

    def _check_hashtag(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.HASHTAG):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data

    def _check_text_link(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(data['pattern'], entity.url):
                return data

    def _check_url(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data

    def _get_filters(self, f_type: FilterType):
        return itertools.chain(
            Filter.get_cache(source=self._source.id, type=f_type.value),
            Filter.get_cache(source=None, type=f_type.value),
        )

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(pattern, string, flags=re.IGNORECASE)
