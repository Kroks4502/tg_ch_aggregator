from pyrogram.types import Message

from models import CategoryMessageHistory, Filter, FilterMessageHistory, Source


def add_to_category_history(
        original_message: Message, category_message: Message,
        source: Source = None, rewritten: bool = False):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)
    CategoryMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        media_group=(original_message.media_group_id
                     if original_message.media_group_id else ''),
        forward_from_chat_id=(original_message.forward_from_chat.id
                              if original_message.forward_from_chat else None),
        forward_from_message_id=original_message.forward_from_message_id,
        category=source.category,
        message_id=category_message.id,
        rewritten=rewritten,
    )


def add_to_filter_history(
        original_message: Message, filter_obj: Filter | int,
        source: Source = None):
    if not source:
        source = Source.get(tg_id=original_message.chat.id)

    FilterMessageHistory.create(
        source=source,
        source_message_id=original_message.id,
        media_group=(original_message.media_group_id
                     if original_message.media_group_id else ''),
        filter=filter_obj
    )
