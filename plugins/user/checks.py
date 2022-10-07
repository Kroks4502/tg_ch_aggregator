import re
from itertools import chain

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from log import logger
from models import Source, Filter
from types import FilterTypes


def perform_filtering(message: Message):
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    source = Source.get(tg_id=message.chat.id)

    inspector = Inspector(source, text)
    if entities:
        for entity in entities:
            if result := inspector.check_entities(entity):
                return result

    if text:
        if result := inspector.check_text():
            return result

    return


class Inspector:
    def __init__(self, source, text):
        self.text = text
        self.source = source

    def check_entity(self, entity) -> int | None:
        if result := self._check_entity_type(entity):
            return result
        if entity.type == MessageEntityType.HASHTAG:
            return self._check_hashtag(entity)
        elif entity.type == MessageEntityType.TEXT_LINK:
            return self._check_text_link(entity)
        elif entity.type == MessageEntityType.URL:
            return self._check_url(entity)

    def _check_entity_type(self, entity):
        ...

    def _check_hashtag(self, entity) -> int | None:
        entity_text = self.text[entity.offset:entity.offset + entity.length]
        data = chain(
            Filter.get_cache(source=self.source, type=FilterTypes.HASHTAG),
            Filter.get_cache(source=None, type=FilterTypes.HASHTAG)
        )
        for filter_id, data in data.items:
            if re.search(data['pattern'], entity_text, flags=re.IGNORECASE):
                return filter_id

    def _check_text_link(self, entity) -> int | None:

        for part_url in ...:
            if re.search(part_url, entity.url, flags=re.IGNORECASE):
                comment = f'#part_of_url: `{part_url}`'
                logger.debug(comment)
                return False, comment

    def _check_url(self, entity) -> int | None:
        for part_url in ...:
            if re.search(
                    part_url,
                    text[entity.offset:entity.offset + entity.length],
                    flags=re.IGNORECASE):
                comment = f'#part_of_url: `{part_url}`'
                logger.debug(comment)
                return False, comment

    def check_reply_markup(self):
        if Filter.global_reply_markup_patterns() + source.get_filter_reply_markup():
            if message.reply_markup:
                comment = f'#reply_markup'
                logger.debug(comment)
                return False, comment

    def check_text(self):
        for part_text in ...:
            if re.search(part_text, text, flags=re.IGNORECASE):
                comment = f'#part_of_text: `{part_text}`'
                logger.debug(comment)
                return False, comment
