import logging
import re
from typing import Any, Iterable

from telethon.tl import types

from filter_types import FilterEntityType, FilterMessageType, FilterType
from models import Filter


class FilterInspector:
    def __init__(
        self,
        source_id: int,
        text: str | None,
    ):
        self.source_id = source_id
        self.text = text

    def check_message_type(self, message: Any) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.MESSAGE_TYPE):
            try:
                if getattr(
                    message,
                    getattr(FilterMessageType, filter_obj.pattern).value[1],
                ):
                    return filter_obj
            except AttributeError as e:
                logging.error(e, exc_info=True)

    def check_white_text(self) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.ONLY_WHITE_TEXT):
            if not self._search(filter_obj.pattern, self.text):
                return filter_obj
        return  # noqa: R502

    def check_text(self) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.TEXT):
            if self._search(filter_obj.pattern, self.text):
                return filter_obj
        return  # noqa: R502

    def check_entities(self, entity: types.TypeMessageEntity) -> Filter | None:
        if result := self._check_entity_type(entity):
            return result

        if isinstance(entity, types.MessageEntityHashtag):
            return self._check_hashtag(entity)
        if isinstance(entity, types.MessageEntityTextUrl):
            return self._check_text_link(entity)
        if isinstance(entity, types.MessageEntityUrl):
            return self._check_url(entity)
        return  # noqa: R502

    def _check_entity_type(self, entity: types.TypeMessageEntity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.ENTITY_TYPE):
            try:
                fet = getattr(FilterEntityType, filter_obj.pattern.upper())
                if isinstance(entity, fet.value[1]):
                    return filter_obj
            except AttributeError as e:
                logging.error(e, exc_info=True)
        return  # noqa: R502

    def _check_hashtag(self, entity: types.TypeMessageEntity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.HASHTAG):
            if self._search(
                filter_obj.pattern,
                self.text[entity.offset : entity.offset + entity.length],
            ):
                return filter_obj
        return  # noqa: R502

    def _check_text_link(self, entity: types.TypeMessageEntity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.URL):
            if self._search(filter_obj.pattern, entity.url):
                return filter_obj
        return  # noqa: R502

    def _check_url(self, entity: types.TypeMessageEntity) -> Filter | None:
        for filter_obj in self._get_filters(FilterType.URL):
            if self._search(
                filter_obj.pattern,
                self.text[entity.offset : entity.offset + entity.length],
            ):
                return filter_obj
        return  # noqa: R502

    def _get_filters(self, f_type: FilterType) -> Iterable[Filter]:
        return Filter.select().where(
            (Filter.type == f_type.value)
            & ((Filter.source == self.source_id) | (Filter.source.is_null()))
        )

    @staticmethod
    def _search(pattern: str, string: str):
        return re.search(pattern, string, flags=re.IGNORECASE)
