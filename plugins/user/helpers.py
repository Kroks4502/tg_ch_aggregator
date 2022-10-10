import itertools
import re

from pyrogram import utils
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from log import logger
from models import Source, CategoryMessageHistory, FilterMessageHistory, Filter
from models_types import FilterType, FilterMessageType


def add_to_category_history(
        original_message: Message, category_message: Message,
        source: Source = None, rewritten: bool = False):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)

    CategoryMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        is_media_group=True if original_message.media_group_id else False,
        forward_from_chat_id=(original_message.forward_from_chat.id
                              if original_message.forward_from_chat else None),
        forward_from_message_id=original_message.forward_from_message_id,
        category=source.category,
        category_message_id=category_message.id,
        rewritten=rewritten,
    )


def add_to_filter_history(
        original_message: Message, filter: Filter | int,
        source: Source = None):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)

    FilterMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        is_media_group=True if original_message.media_group_id else False,
        filter=filter
    )


def get_message_link(chat_id: int, message_id: int):
    return f'https://t.me/c/{utils.get_channel_id(chat_id)}/{message_id}'


def perform_check_history(message: Message, source: Source) -> CategoryMessageHistory | None:
    if message.forward_from_chat:
        forward_source = Source.get_or_none(tg_id=message.forward_from_chat.id)
        if forward_source:
            if h_obj := CategoryMessageHistory.get_or_none(
                    category=source.category,
                    source=forward_source,
                    source_message_id=message.forward_from_message_id
            ):
                return h_obj

        if h_obj := CategoryMessageHistory.get_or_none(
                category=source.category,
                forward_from_chat_id=message.forward_from_chat.id,
                forward_from_message_id=message.forward_from_message_id
        ):
            return h_obj

    else:
        if h_obj := CategoryMessageHistory.get_or_none(
                category=source.category,
                source=source,
                source_message_id=message.id
        ):
            return h_obj

        if h_obj := CategoryMessageHistory.get_or_none(
                category=source.category,
                forward_from_chat_id=message.chat.id,
                forward_from_message_id=message.id
        ):
            return h_obj


def perform_filtering(message: Message, source: Source) -> int | None:
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
                if getattr(self._message, getattr(FilterMessageType, data['pattern']).value[1]):
                    return data['id']
            except AttributeError as e:
                logger.error(e, exc_info=True)

    def check_white_text(self) -> int | None:
        for data in self._get_filters(FilterType.ONLY_WHITE_TEXT):
            if not self._search(
                    data['pattern'],
                    self._text):
                return data['id']

    def check_text(self) -> int | None:
        for data in self._get_filters(FilterType.TEXT):
            if self._search(
                    data['pattern'],
                    self._text):
                return data['id']

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
                if entity.type == getattr(
                        MessageEntityType, data['pattern'].upper()):
                    return data['id']
            except AttributeError as e:
                logger.error(e, exc_info=True)

    def _check_hashtag(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.HASHTAG):
            if self._search(
                    data['pattern'],
                    self._text[entity.offset:entity.offset + entity.length]):
                return data['id']

    def _check_text_link(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(
                    data['pattern'],
                    entity.url):
                return data['id']

    def _check_url(self, entity: MessageEntity) -> int | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(
                    data['pattern'],
                    self._text[entity.offset:entity.offset + entity.length]):
                return data['id']

    def _get_filters(self, f_type: FilterType):
        return itertools.chain(
            Filter.get_cache(source=self._source, type=f_type),
            Filter.get_cache(source=None, type=f_type))

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(
            pattern,
            string,
            flags=re.IGNORECASE)
