from operator import attrgetter

from pyrogram.types import Message

from clients import user_client
from models import Source
from plugins.user.sources_monitoring.new_message import new_message


async def processing_unread_messages_job():
    """Обработка непрочитанных сообщений UserBot."""
    unread_messages = await get_unread_messages()
    for message in sorted(unread_messages, key=attrgetter("date")):
        await new_message(user_client, message)


async def get_unread_messages() -> list[Message]:
    """
    Получить непрочитанные сообщения UserBot.
    Возвращается только по одному сообщению каждой медиа-группы.
    """
    sources_ids = {
        source.id
        for source in Source.select(Source.id).where(Source.is_deleted == False)
    }

    unread_messages = []
    async for dialog in user_client.get_dialogs():
        if dialog.unread_messages_count == 0 or dialog.chat.id not in sources_ids:
            continue

        media_group_ids = set()
        async for message in user_client.get_chat_history(
            chat_id=dialog.chat.id,
            limit=dialog.unread_messages_count,
        ):
            if not message.media_group_id:
                unread_messages.append(message)
                continue

            if message.media_group_id not in media_group_ids:
                media_group_ids.add(message.media_group_id)
                unread_messages.append(message)

    return unread_messages
