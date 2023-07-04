import itertools
import logging
import re
from typing import Iterable

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message, MessageEntity

from filter_types import FilterMessageType, FilterType
from models import Filter, MessageHistory, Source


def get_filter_id_or_none(message: Message, source: Source) -> int | None:
    """
    Получить фильтр под который подходит текст сообщения.
    """
    if data := check_message_filter(message, source):
        return data['id']

    return


def get_history_id_or_none(message: Message, category_id: int) -> int | None:
    """Получить id истории сообщения."""
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

    history_obj = get_history_obj_or_none(
        category_id=category_id,
        source_chat_id=source_chat_id,
        source_message_id=source_message_id,
        forward_from_chat_id=forward_from_chat_id,
        forward_from_message_id=forward_from_message_id,
    )
    if history_obj:
        return history_obj.id
    return


def get_history_obj_or_none(
    category_id: int,
    source_chat_id: int,
    source_message_id: int,
    forward_from_chat_id: int,
    forward_from_message_id: int,
) -> MessageHistory | None:
    """Получить объект истории сообщения."""
    try:
        mh: type[MessageHistory] = MessageHistory.alias()
        history_obj = (
            mh.select(mh.id)
            .where(
                (
                    mh.category_id == category_id
                )  # Все проверки выполняем в рамках одной категории
                & (
                    (
                        (mh.source_id == source_chat_id)
                        & (mh.source_message_id == source_message_id)
                    )
                    | (
                        (mh.source_forward_from_chat_id == forward_from_chat_id)
                        & (mh.source_forward_from_message_id == forward_from_message_id)
                    )
                )
                & (
                    mh.category_message_id
                    != None  # noqa E711 Отсутствующие сообщения в категории не учитываем
                )
            )
            .get()
        )  # Работает по индексам

        return history_obj
    except MessageHistory.DoesNotExist:
        return


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
