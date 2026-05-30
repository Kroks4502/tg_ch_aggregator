"""
Обработчик сервисных сообщений в источниках (Telethon).

Сервисные сообщения (pin, join, leave, etc.) просто помечаются прочитанными.
"""

from telethon import events

from plugins.user.sources_monitoring.common import is_monitored_filter


async def on_service_message(event: events.NewMessage.Event):
    """Пометить сервисное сообщение в источнике прочитанным."""
    if not await is_monitored_filter(event):
        return
    try:
        await event.client.send_read_acknowledge(event.chat_id, max_id=event.message.id)
    except Exception:
        pass
