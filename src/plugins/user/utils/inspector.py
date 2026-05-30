import logging
import re
from typing import Iterable

from telethon.tl.types import (
    MessageEntityBankCard,
    MessageEntityBlockquote,
    MessageEntityBold,
    MessageEntityBotCommand,
    MessageEntityCashtag,
    MessageEntityCode,
    MessageEntityCustomEmoji,
    MessageEntityEmail,
    MessageEntityHashtag,
    MessageEntityItalic,
    MessageEntityMention,
    MessageEntityMentionName,
    MessageEntityPhone,
    MessageEntityPre,
    MessageEntitySpoiler,
    MessageEntityStrike,
    MessageEntityTextUrl,
    MessageEntityUnderline,
    MessageEntityUnknown,
    MessageEntityUrl,
)

from filter_types import FilterMessageType, FilterType
from models import Filter

# Маппинг: имя FilterEntityType → Telethon-класс сущности
_ENTITY_TYPE_MAP: dict[str, type] = {
    "MENTION": MessageEntityMention,
    "HASHTAG": MessageEntityHashtag,
    "CASHTAG": MessageEntityCashtag,
    "BOT_COMMAND": MessageEntityBotCommand,
    "URL": MessageEntityUrl,
    "EMAIL": MessageEntityEmail,
    "PHONE_NUMBER": MessageEntityPhone,
    "BOLD": MessageEntityBold,
    "ITALIC": MessageEntityItalic,
    "UNDERLINE": MessageEntityUnderline,
    "STRIKETHROUGH": MessageEntityStrike,
    "SPOILER": MessageEntitySpoiler,
    "CODE": MessageEntityCode,
    "PRE": MessageEntityPre,
    "BLOCKQUOTE": MessageEntityBlockquote,
    "TEXT_LINK": MessageEntityTextUrl,
    "TEXT_MENTION": MessageEntityMentionName,
    "BANK_CARD": MessageEntityBankCard,
    "CUSTOM_EMOJI": MessageEntityCustomEmoji,
    "UNKNOWN": MessageEntityUnknown,
}


def _get_msg_text(message) -> str | None:
    """Текст или подпись сообщения (Telethon хранит в одном поле message.text)."""
    return message.text or None


def _get_msg_type_attr(message, attr_name: str):
    """
    Получить атрибут сообщения для проверки FilterMessageType.
    Обрабатывает специальный случай CAPTION (в Telethon нет отдельного caption).
    """
    if attr_name == "caption":
        # CAPTION в Telethon: text присутствует И это медиа-сообщение
        return message.text if message.media is not None else None
    return getattr(message, attr_name, None)


class FilterInspector:
    def __init__(self, message, source_id: int):
        self._message = message
        self._text = _get_msg_text(message)
        self._source_id = source_id

    def check_message_type(self) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.MESSAGE_TYPE):
            try:
                attr_name = FilterMessageType[filter_obj.pattern].value[1]
                if _get_msg_type_attr(self._message, attr_name):
                    return filter_obj
            except (AttributeError, KeyError) as e:
                logging.error(e, exc_info=True)
        return None

    def check_white_text(self) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.ONLY_WHITE_TEXT):
            if not self._search(filter_obj.pattern, self._text):
                return filter_obj
        return  # noqa: R502

    def check_text(self) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.TEXT):
            if self._search(filter_obj.pattern, self._text):
                return filter_obj
        return  # noqa: R502

    def check_entities(self, entity) -> Filter | None:
        if result := self._check_entity_type(entity):
            return result

        if isinstance(entity, MessageEntityHashtag):
            return self._check_hashtag(entity)
        if isinstance(entity, MessageEntityTextUrl):
            return self._check_text_link(entity)
        if isinstance(entity, MessageEntityUrl):
            return self._check_url(entity)
        return  # noqa: R502

    def _check_entity_type(self, entity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.ENTITY_TYPE):
            cls = _ENTITY_TYPE_MAP.get(filter_obj.pattern.upper())
            if cls and isinstance(entity, cls):
                return filter_obj
        return  # noqa: R502

    def _check_hashtag(self, entity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.HASHTAG):
            if self._search(
                filter_obj.pattern,
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return filter_obj
        return  # noqa: R502

    def _check_text_link(self, entity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.URL):
            if self._search(filter_obj.pattern, entity.url):
                return filter_obj
        return  # noqa: R502

    def _check_url(self, entity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.URL):
            if self._search(
                filter_obj.pattern,
                self._text[entity.offset : entity.offset + entity.length],
            ):
                return filter_obj
        return  # noqa: R502

    def _get_filters(self, f_type: FilterType) -> Iterable[Filter]:
        return Filter.select().where(
            (Filter.type == f_type.value) & ((Filter.source == self._source_id) | (Filter.source.is_null()))
        )

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(pattern, string, flags=re.IGNORECASE)
