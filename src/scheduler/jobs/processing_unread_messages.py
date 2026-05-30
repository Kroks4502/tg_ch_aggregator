import logging

from clients import telethon_user_client
from models import Source
from plugins.user.sources_monitoring.new_message import handle_new_messages

logger = logging.getLogger(__name__)


async def processing_unread_messages_job():
    """Обработка непрочитанных сообщений UserBot."""
    logger.debug("Starting job...")
    groups = await _get_unread_message_groups()
    logger.info("Found %d message groups (singles + albums)", len(groups))
    for messages in groups:
        logger.debug("Processing group of %d message(s), first id=%s", len(messages), messages[0].id)
        await handle_new_messages(telethon_user_client, messages)
    logger.debug("Job completed")


async def _get_unread_message_groups() -> list[list]:
    """
    Получить непрочитанные сообщения из источников, сгруппированные по альбомам.

    Возвращает список групп, каждая группа = [message] для одиночного
    или [msg1, msg2, ...] для альбома, отсортированный по дате первого сообщения.
    """
    logger.debug("Getting unread messages...")

    sources_ids: set[int] = {
        source.id
        for source in Source.select(Source.id).where(Source.is_deleted == False)
    }

    albums: dict[int, list] = {}   # grouped_id → сообщения
    singles: list[list] = []

    async for dialog in telethon_user_client.iter_dialogs():
        if dialog.unread_count == 0 or dialog.id not in sources_ids:
            continue
        logger.debug(
            "Dialog %s has %d unread messages",
            dialog.id, dialog.unread_count,
        )

        async for msg in telethon_user_client.iter_messages(
            dialog.id,
            limit=dialog.unread_count,
        ):
            if not msg.grouped_id:
                singles.append([msg])
            else:
                albums.setdefault(msg.grouped_id, []).append(msg)

    # Сортируем части альбомов по message.id (порядок публикации)
    album_groups = [sorted(msgs, key=lambda m: m.id) for msgs in albums.values()]

    all_groups = singles + album_groups
    # Сортируем все группы по дате первого сообщения (oldest first)
    return sorted(all_groups, key=lambda msgs: msgs[0].date)
