import asyncio
import logging
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)


class AlbumCollector:
    """
    Буферизует сообщения медиа-группы Telethon и вызывает callback после сбора всех частей.

    Telethon генерирует отдельное событие на каждое сообщение в альбоме (по одному),
    в отличие от pyrogram, где message.get_media_group() возвращает весь список сразу.
    Для корректной обработки альбома нужно подождать остальные части перед вызовом пайплайна.

    Использование (в new_message-хендлере):
        if message.grouped_id is not None:
            await album_collector.add(
                chat_id=event.chat_id,
                grouped_id=message.grouped_id,
                message=message,
                callback=lambda msgs: handle_album(client, msgs),
            )
        else:
            await handle_single(client, message)
    """

    TIMEOUT: float = 0.5  # сек — ожидание отставших сообщений группы

    def __init__(self) -> None:
        # (chat_id, grouped_id) → список накопленных сообщений
        self._buffers: dict[tuple[int, int], list[Any]] = {}
        # (chat_id, grouped_id) → задача сброса буфера
        self._tasks: dict[tuple[int, int], asyncio.Task] = {}

    async def add(
        self,
        chat_id: int,
        grouped_id: int,
        message: Any,
        callback: Callable,
    ) -> None:
        """
        Добавить сообщение в буфер альбома.

        :param chat_id: ID чата-источника (message.chat_id).
        :param grouped_id: grouped_id медиа-группы (message.grouped_id).
        :param message: Объект сообщения Telethon.
        :param callback: Async callable(messages: list) — вызывается, когда
                         буфер сброшен (таймаут истёк без новых сообщений группы).
        """
        key = (chat_id, grouped_id)
        self._buffers.setdefault(key, []).append(message)

        # Сбрасываем таймер: каждое новое сообщение в группе откладывает сброс
        if key in self._tasks:
            self._tasks[key].cancel()

        async def _flush() -> None:
            try:
                await asyncio.sleep(self.TIMEOUT)
            except asyncio.CancelledError:
                return

            messages = sorted(self._buffers.pop(key, []), key=lambda m: m.id)
            self._tasks.pop(key, None)

            if not messages:
                return

            log.debug(
                "AlbumCollector: grouped_id=%s chat=%s — сброс %d сообщений",
                grouped_id,
                chat_id,
                len(messages),
            )
            await callback(messages)

        self._tasks[key] = asyncio.create_task(_flush())
