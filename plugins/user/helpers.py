from pyrogram.types import Message

from models import Source, CategoryMessageHistory, FilterMessageHistory, Filter


def add_to_category_history(
        original_message: Message, category_message: Message,
        source: Source = None, rewritten: bool = False):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)

    CategoryMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        is_media_group=True if original_message.media_group_id else False,
        category_message_id=category_message.id,
        rewritten=rewritten,
    )


def add_to_filter_history(
        original_message: Message, filter: Filter,
        source: Source = None):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)

    FilterMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        is_media_group=True if original_message.media_group_id else False,
        filter=filter
    )
