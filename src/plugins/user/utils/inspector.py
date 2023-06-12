import itertools
import logging
import re
from typing import Iterable

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from common import get_shortened_text
from filter_types import FilterMessageType, FilterType
from models import CategoryMessageHistory, Filter, Source
from plugins.user.utils.history import add_to_filter_history


def is_new_and_valid_post(message: Message, source: Source) -> bool:
    """Сообщения ещё нет в истории и оно проходит фильтр."""
    if not is_new_post(message, source.category_id):
        logging.info(
            f'Сообщение {message.id} из источника '
            f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'{"в составе медиагруппы " + str(message.media_group_id) + " " if message.media_group_id else ""}'
            'уже есть в канале категории'
            f' {get_shortened_text(source.category.title, 20)} {source.category.tg_id}'
            f'ИЛИ было отфильтровано.'
        )
        return False

    if data := check_message_filter(message, source):
        add_to_filter_history(message, data['id'], source)
        logging.info(
            f'Сообщение {message.id} из источника '
            f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
            f'{"в составе медиагруппы " + str(message.media_group_id) + " " if message.media_group_id else ""}'
            f'отфильтровано: {data}'
        )
        return False

    return True


def is_new_post(message: Message, category_id: int) -> bool:
    """Проверка уникальности сообщения."""
    if message.forward_from_chat:
        # Сообщение переслано в источник из другого чата

        # Сообщение уже может быть в истории по этому чату, если он является источником
        source_chat_id = message.forward_from_chat.id
        source_message_id = message.forward_from_message_id

        # Проверяем не пересылалось ли уже в других источниках это сообщение
        forward_from_chat_id = message.forward_from_chat.id
        forward_from_message_id = message.forward_from_message_id
    else:  # Сообщение не является пересланным
        # Проверяем наличие этого сообщения в истории
        source_chat_id = message.chat.id
        source_message_id = message.id

        # Проверяем не получили ли мы это сообщение ранее как пересланное из другого источника
        forward_from_chat_id = message.chat.id
        forward_from_message_id = message.id

    if not (forward_from_chat_id and forward_from_message_id):
        # todo: Временная проверка, что forward_from_chat_id и forward_from_message_id всегда есть
        #   (SQL('TRUE') if forward_from_chat_id else SQL('FALSE'))
        logging.error(
            'forward_from_chat_id и forward_from_message_id должны быть всегда для выполнения запроса по индексам!'
        )

    h_a = CategoryMessageHistory.alias()
    h_obj = h_a.select().where(
        (
            h_a.category_id == category_id
        )  # Все проверки выполняем в рамках одной категории
        & (
            (
                (h_a.source_chat_id == source_chat_id)
                & (h_a.source_message_id == source_message_id)
            )
            | (
                (h_a.forward_from_chat_id == forward_from_chat_id)
                & (h_a.forward_from_message_id == forward_from_message_id)
            )
        )
        & ~h_a.deleted  # Удаленные сообщения не учитываем
    )  # Работает по индексам

    if h_obj.exists():
        return False

    return True


def check_message_filter(message: Message, source: Source) -> dict | None:
    """Получить информацию о прохождении фильтра, если сообщение его не проходит."""

    inspector = FilterInspector(message, source)

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


class FilterInspector:
    def __init__(self, message: Message, source: Source):
        self._message = message
        self._text = message.text or message.caption
        self._source = source

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
        return

    def check_text(self) -> dict | None:
        for data in self._get_filters(FilterType.TEXT):
            if self._search(data['pattern'], self._text):
                return data
        return

    def check_entities(self, entity: MessageEntity) -> dict | None:
        if result := self._check_entity_type(entity):
            return result

        if entity.type == MessageEntityType.HASHTAG:
            return self._check_hashtag(entity)
        if entity.type == MessageEntityType.TEXT_LINK:
            return self._check_text_link(entity)
        if entity.type == MessageEntityType.URL:
            return self._check_url(entity)
        return

    def _check_entity_type(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.ENTITY_TYPE):
            try:
                if entity.type == getattr(MessageEntityType, data['pattern'].upper()):
                    return data
            except AttributeError as e:
                logging.error(e, exc_info=True)
        return

    def _check_hashtag(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.HASHTAG):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data
        return

    def _check_text_link(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(data['pattern'], entity.url):
                return data
        return

    def _check_url(self, entity: MessageEntity) -> dict | None:
        for data in self._get_filters(FilterType.URL):
            if self._search(
                data['pattern'],
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return data
        return

    def _get_filters(self, f_type: FilterType) -> Iterable[dict]:
        return itertools.chain(
            Filter.get_cache(source=self._source.id, type=f_type.value),
            Filter.get_cache(source=None, type=f_type.value),
        )

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(pattern, string, flags=re.IGNORECASE)
