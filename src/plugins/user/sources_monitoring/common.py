"""
Общие утилиты для обработки сообщений из источников (Telethon).
"""

import logging

from async_lru import alru_cache
from peewee import DoesNotExist
from telethon.tl.types import MessageMediaDocument, MessageMediaPhoto

from models import MessageHistory, Source
from plugins.user.exceptions import (
    MessageBlockedByIdError,
    MessageBlockedByMediaGroupError,
    MessageMediaWithoutCaptionError,
)
from plugins.user.types import Operation
from plugins.user.utils.chats_locks import ChatsLocks, MessagesLocks
from plugins.user.utils.inspector import FilterInspector
from plugins.user.utils.rewriter.footer import LINK_TEXT, FooterController
from plugins.user.utils.rewriter.header import (
    FWD_TEXT_TMPL,
    FWD_USR_TEXT_TMPL,
    SRC_TEXT_TMPL,
    HeaderController,
)
from plugins.user.utils.telethon_helpers import (
    get_fwd_from_name,
    get_fwd_origin,
    get_message_link,
    msg_entities,
    msg_text,
)
from plugins.user.utils.text_length import tg_len
from settings import TELEGRAM_MAX_CAPTION_LENGTH, TELEGRAM_MAX_TEXT_LENGTH

blocking_messages = ChatsLocks("all")

log = logging.getLogger(__name__)


def set_blocking(operation: Operation, message, block_value: int) -> MessagesLocks:
    """
    Установить блокировку для сущности.

    :param operation: Производимая операция (для исключения).
    :param message: Сообщение источника.
    :param block_value: ID для блокировки (message.id или message.grouped_id).
    :raise MessageBlockedByMediaGroupError: Сообщение заблокировано в составе медиагруппы.
    :raise MessageBlockedByIdError: Сообщение заблокировано по ID.
    """
    blocked = blocking_messages.get(key=message.chat_id)
    if blocked.contains(key=message.grouped_id):
        raise MessageBlockedByMediaGroupError(operation=operation, message=message, blocked=blocked)
    if blocked.contains(key=message.id):
        raise MessageBlockedByIdError(operation=operation, message=message, blocked=blocked)
    blocked.add(value=block_value)
    return blocked


def get_filter_id_or_none(message, source_id: int) -> int | None:
    """Получить ID фильтра, который не прошёл текст сообщения."""
    inspector = FilterInspector(message=message, source_id=source_id)

    if filter_obj := inspector.check_message_type():
        return filter_obj.id

    if msg_text(message):
        if filter_obj := inspector.check_white_text():
            return filter_obj.id
        if filter_obj := inspector.check_text():
            return filter_obj.id

    entities = msg_entities(message)
    if entities:
        for entity in entities:
            if filter_obj := inspector.check_entities(entity):
                return filter_obj.id

    return  # noqa: R502


def get_input_media_for_album(message):
    """
    Преобразовать медиа сообщения в InputMedia для send_album_with_entities.
    Вынесено в telethon_helpers._get_album_input_media — здесь просто alias.
    """
    from plugins.user.utils.telethon_helpers import _get_album_input_media

    return _get_album_input_media(message)


def cut_long_message(message) -> None:
    """Обрезать текст/подпись если превышает лимит Telegram."""
    text = msg_text(message)
    if not text:
        return

    is_media = message.media is not None
    max_len = TELEGRAM_MAX_CAPTION_LENGTH if is_media else TELEGRAM_MAX_TEXT_LENGTH

    if tg_len(text) <= max_len:
        return

    fwd_origin = get_fwd_origin(message)
    if fwd_origin:
        fwd_chat_id, fwd_msg_id = fwd_origin
        link_url = f"https://t.me/c/{abs(fwd_chat_id) - 10**12}/{fwd_msg_id}"
    else:
        link_url = get_message_link(message.chat_id, message.id)

    footer = FooterController()
    footer.add_item(text=LINK_TEXT, url=link_url, bold=True)
    footer.include_to_message(message=message)


async def add_header(client, source: Source, message) -> None:
    """
    Добавить заголовок к сообщению (источник + forward-origin если есть).

    Async, т.к. может потребоваться разрешение entity для получения названия
    forward-источника через Telethon.
    """
    header = HeaderController(item_separator="\n")
    header.add_item(
        text=SRC_TEXT_TMPL.format(source.title_alias or source.title or str(message.chat_id)),
        bold=True,
        url=get_message_link(message.chat_id, message.id),
    )

    fwd_origin = get_fwd_origin(message)
    if fwd_origin:
        fwd_chat_id, fwd_msg_id = fwd_origin
        fwd_title = await _get_fwd_title(client, fwd_chat_id)
        fwd_link = _get_fwd_link_by_ids(fwd_chat_id, fwd_msg_id, entity=None)
        # Пробуем получить username для красивой ссылки
        try:
            fwd_entity = await _get_cached_entity(client, fwd_chat_id)
            if fwd_entity:
                fwd_username = getattr(fwd_entity, "username", None)
                if fwd_username:
                    fwd_link = f"https://t.me/{fwd_username}/{fwd_msg_id}"
        except Exception:
            pass
        header.add_item(text=FWD_TEXT_TMPL.format(fwd_title), url=fwd_link)

    elif name := get_fwd_from_name(message):
        # Пользователь скрыл ID при пересылке — только имя, без ссылки
        header.add_item(text=FWD_USR_TEXT_TMPL.format(name))

    elif message.fwd_from and message.fwd_from.from_id:
        # Переслано от пользователя с известным ID
        try:
            sender = await client.get_entity(message.fwd_from.from_id)
            first = getattr(sender, "first_name", "") or ""
            last = getattr(sender, "last_name", "") or ""
            full_name = f"{first} {last}".strip() or str(message.fwd_from.from_id)
            username = getattr(sender, "username", None)
            url = f"https://t.me/{username}" if username else None
            header.add_item(text=FWD_USR_TEXT_TMPL.format(full_name), url=url)
        except Exception:
            pass

    header.include_to_message(message=message, end_text="\n\n")


def is_media_message_with_caption(operation: Operation, message) -> bool:
    """
    True — сообщение является медиа с возможностью подписи.

    :raise MessageMediaWithoutCaptionError: медиа без поддержки подписи.
    """
    if message.text:
        return False

    if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
        return True

    raise MessageMediaWithoutCaptionError(operation=operation, message=message)


def get_reply_to(message) -> int | None:
    """
    Получить ID сообщения в категории, на которое нужно ответить.

    Если сообщение-источник было ответом на другое сообщение, ищем его
    соответствие в MessageHistory → возвращаем category_message_id.
    """
    if not message.reply_to:
        return None

    reply_msg_id = message.reply_to.reply_to_msg_id
    if not reply_msg_id:
        return None

    try:
        history_msg = MessageHistory.get(
            (MessageHistory.source_id == message.chat_id)
            & (MessageHistory.source_message_id == reply_msg_id)
            & MessageHistory.category_message_id.is_null(False)
            & MessageHistory.deleted_at.is_null()
        )
        return history_msg.category_message_id
    except DoesNotExist:
        return None


# ---------------------------------------------------------------------------
# Внутренние хелперы
# ---------------------------------------------------------------------------


@alru_cache(ttl=300)
async def _get_cached_entity(client, peer_id: int):
    """Получить сущность по marked peer_id с кешированием 5 мин."""
    try:
        return await client.get_entity(peer_id)
    except Exception as e:
        log.debug("_get_cached_entity(%s): %s", peer_id, e)
        return None


async def _get_fwd_title(client, fwd_chat_id: int) -> str:
    """Получить название канала-источника пересылки."""
    entity = await _get_cached_entity(client, fwd_chat_id)
    if entity:
        return getattr(entity, "title", None) or str(fwd_chat_id)
    return str(fwd_chat_id)


def _get_fwd_link_by_ids(fwd_chat_id: int, fwd_msg_id: int, entity=None) -> str:
    """Сформировать ссылку на оригинальное сообщение пересылки."""
    bare_id = abs(fwd_chat_id) - 10**12
    return f"https://t.me/c/{bare_id}/{fwd_msg_id}"


@alru_cache(ttl=60)
async def _get_active_source_ids() -> frozenset:
    """Получить множество ID активных источников (с кешированием 60 сек)."""
    return frozenset(row[0] for row in Source.select(Source.id).where(Source.is_deleted == False).tuples())


async def is_monitored_filter(event) -> bool:
    """Telethon event filter: пропускает только события из активных источников."""
    chat_id = getattr(event, "chat_id", None)
    if chat_id is None:
        return False
    return chat_id in await _get_active_source_ids()
