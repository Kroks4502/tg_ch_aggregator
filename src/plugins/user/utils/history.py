from pyrogram.types import Message

from models import CategoryMessageHistory, Filter, FilterMessageHistory, Source


def add_to_category_history(
    source_message: Message,
    category_message: Message,
    source: Source = None,
    rewritten: bool = False,
):
    if not source:
        source = Source.get(tg_id=source_message.chat.id)

    CategoryMessageHistory.create(
        source=source,
        source_chat_id=source_message.chat.id,
        source_message_id=source_message.id,
        media_group=source_message.media_group_id or '',
        forward_from_chat_id=(
            source_message.forward_from_chat.id
            if source_message.forward_from_chat
            else None
        ),
        forward_from_message_id=source_message.forward_from_message_id,
        category_id=source.category_id,
        message_id=category_message.id,
        rewritten=rewritten,
    )


def add_to_filter_history(
    message: Message,
    filter_obj: Filter | int,
    source: Source = None,
):
    if not source:
        source = Source.get(tg_id=message.chat.id)

    FilterMessageHistory.create(
        source=source,
        source_chat_id=message.chat.id,
        source_message_id=message.id,
        media_group=message.media_group_id or '',
        filter=filter_obj,
    )
