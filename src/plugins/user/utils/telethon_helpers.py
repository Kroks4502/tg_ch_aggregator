"""
Утилиты для работы с Telethon-клиентом userbot'а.

Весь Telethon-специфичный код — маппинг атрибутов сообщений, отправка медиа-групп
с сохранением entities, копирование сообщений — сосредоточен здесь, чтобы
хендлеры и утилиты (cleanup, rewriter) не зависели напрямую от Telethon API.

Используется начиная с этапа 2 миграции (PR-6), когда pyrogram userbot заменяется
на Telethon. В PR-5 файл только создаётся без подключения к основному коду.
"""

import random as _random
import logging

from telethon import utils as _tl_utils
from telethon.tl import types as _tl_types
from telethon.tl.functions.messages import (
    EditMessageRequest as _EditMessageRequest,
    SendMultiMediaRequest as _SendMultiMediaRequest,
)
from telethon.tl.types import InputSingleMedia as _InputSingleMedia

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Работа с атрибутами сообщений
# ---------------------------------------------------------------------------

def msg_text(message) -> str | None:
    """
    Текст сообщения или подпись медиа.

    В Telethon и текст, и подпись хранятся в одном поле message.message
    (доступно как message.text). Возвращает None, если поле пустое.
    """
    return message.text or None


def msg_entities(message) -> list | None:
    """
    Entities форматирования (для текста и для подписи медиа).

    В Telethon хранятся в message.entities независимо от типа сообщения.
    """
    return message.entities or None


def msg_has_media(message) -> bool:
    """
    True, если сообщение содержит медиа (фото, видео, документ, аудио и т.п.).

    В Telethon признак медиа — message.media is not None.
    Аналог проверки message.caption is not None в pyrogram.
    """
    return message.media is not None


def set_msg_text(message, text: str | None, entities: list | None) -> None:
    """
    Установить текст/подпись и entities сообщения (мутирует объект).

    Telethon сообщения — обычные Python-объекты; поле message.message
    доступно для записи напрямую.

    :param message: Объект сообщения Telethon.
    :param text: Новый текст/подпись. None или пустая строка → "".
    :param entities: Новый список entities. None → [].
    """
    message.message = text or ""
    message.entities = entities or []


# ---------------------------------------------------------------------------
# Ссылки и идентификаторы
# ---------------------------------------------------------------------------

def get_message_link(chat_id: int, msg_id: int) -> str:
    """
    Ссылка на сообщение в закрытом канале/супергруппе.

    Для chat_id вида -100XXXXXXXXXX берём XXXXXXXXXX (bare channel id).
    """
    bare_id = abs(chat_id) - 10 ** 12
    return f"https://t.me/c/{bare_id}/{msg_id}"


def get_fwd_origin(message) -> tuple[int, int] | None:
    """
    Определить оригинальный источник пересланного сообщения.

    :return: (fwd_chat_id, fwd_msg_id) в формате -100XXXXXXXXXX или None,
             если сообщение не переслано из канала.
    """
    if not message.fwd_from:
        return None

    from_id = message.fwd_from.from_id
    channel_post = message.fwd_from.channel_post

    # Нас интересует только пересылка из канала с конкретным message_id
    if from_id is None or channel_post is None:
        return None

    try:
        fwd_chat_id = _tl_utils.get_peer_id(from_id)
    except Exception:
        log.debug("get_fwd_origin: не удалось получить peer_id из %s", from_id)
        return None

    return fwd_chat_id, channel_post


def get_fwd_from_name(message) -> str | None:
    """
    Имя отправителя при пересылке (аналог message.forward_sender_name в pyrogram).

    Используется, когда пользователь скрыл свой ID в настройках приватности.
    """
    if not message.fwd_from:
        return None
    return message.fwd_from.from_name or None


# ---------------------------------------------------------------------------
# Копирование и пересылка
# ---------------------------------------------------------------------------

async def copy_message(
    client,
    target_chat_id: int,
    message,
    *,
    reply_to: int | None = None,
    disable_notification: bool = False,
) -> object:
    """
    Скопировать сообщение без заголовка «Переслано из».
    Аналог pyrogram's message.copy(chat_id).

    Для текстовых сообщений — send_message с formatting_entities.
    Для медиа — send_file с formatting_entities (caption_entities).

    :param client: TelegramClient (userbot).
    :param target_chat_id: Чат-получатель (chat_id агрегатора).
    :param message: Объект сообщения Telethon.
    :param reply_to: ID сообщения, на которое отвечаем, или None.
    :param disable_notification: True — без звука.
    :return: Отправленное сообщение Telethon.
    """
    if not msg_has_media(message):
        return await client.send_message(
            entity=target_chat_id,
            message=msg_text(message) or "",
            formatting_entities=msg_entities(message),
            link_preview=False,
            silent=disable_notification,
            reply_to=reply_to,
        )

    return await client.send_file(
        entity=target_chat_id,
        file=message.media,
        caption=msg_text(message),
        formatting_entities=msg_entities(message),
        silent=disable_notification,
        reply_to=reply_to,
    )


async def forward_messages(
    client,
    target_chat_id: int,
    source_chat_id: int,
    message_ids: list[int],
    *,
    disable_notification: bool = False,
) -> list:
    """
    Переслать список сообщений с заголовком «Переслано из».
    Аналог pyrogram's client.forward_messages(...).

    :return: Список пересланных сообщений Telethon.
    """
    return await client.forward_messages(
        entity=target_chat_id,
        messages=message_ids,
        from_peer=source_chat_id,
        silent=disable_notification,
    )


# ---------------------------------------------------------------------------
# Медиа-группы (raw TL для сохранения entities)
# ---------------------------------------------------------------------------

def _get_album_input_media(message):
    """
    Преобразовать медиа сообщения в InputMedia для SendMultiMedia.

    Сохраняет spoiler-атрибут (если есть).
    Аналог логики в pyrogram_fork/send_media_group.py.
    """
    media = message.media
    if media is None:
        raise ValueError(f"Сообщение {message.id} не содержит медиа")

    spoiler: bool = getattr(media, "spoiler", False) or False

    if isinstance(media, _tl_types.MessageMediaPhoto):
        return _tl_types.InputMediaPhoto(
            id=_tl_utils.get_input_photo(media.photo),
            spoiler=spoiler,
        )

    if isinstance(media, _tl_types.MessageMediaDocument):
        return _tl_types.InputMediaDocument(
            id=_tl_utils.get_input_document(media.document),
            spoiler=spoiler,
        )

    # Fallback для других медиа-типов (без поддержки spoiler)
    return _tl_utils.get_input_media(media)


async def send_album_with_entities(
    client,
    target_chat_id: int,
    messages: list,
    *,
    disable_notification: bool = False,
) -> list:
    """
    Отправить медиа-группу с сохранением entities (caption_entities) для каждого сообщения.

    Использует низкоуровневый SendMultiMediaRequest — аналог
    pyrogram_fork/send_media_group.py:SendMediaGroup.send_media_group.

    :param client: TelegramClient (userbot).
    :param target_chat_id: Чат-получатель.
    :param messages: Список сообщений Telethon (уже обработанных: cleanup, header).
    :param disable_notification: True — без звука.
    :return: Список отправленных сообщений Telethon.
    """
    peer = await client.get_input_entity(target_chat_id)

    multi_media = [
        _InputSingleMedia(
            media=_get_album_input_media(msg),
            random_id=_random.randrange(-(2 ** 63), 2 ** 63),
            message=msg_text(msg) or "",
            entities=msg_entities(msg) or [],
        )
        for msg in messages
    ]

    request = _SendMultiMediaRequest(
        peer=peer,
        multi_media=multi_media,
        silent=disable_notification,
    )
    result = await client(request)

    # Telethon конвертирует Updates → список Message через _get_response_message
    sent = client._get_response_message(request, result, peer)

    # _get_response_message возвращает один объект или список
    if not isinstance(sent, list):
        sent = [sent] if sent is not None else []

    return sent


def tl_message_to_dict(message) -> dict:
    """
    Минимальный JSON-сериализуемый снимок сообщения Telethon для сохранения в history.data.

    Заменяет json.loads(message.__str__()) из pyrogram, которое давало полный JSON.
    Хранится только то, что нужно для диагностики.
    """
    return {
        "id": message.id,
        "date": message.date.isoformat() if message.date else None,
        "edit_date": message.edit_date.isoformat() if getattr(message, "edit_date", None) else None,
        "text": message.text or None,
        "chat_id": getattr(message, "chat_id", None),
        "grouped_id": getattr(message, "grouped_id", None),
        "is_media": message.media is not None if hasattr(message, "media") else False,
    }


async def edit_message_with_entities(
    client,
    chat_id: int,
    msg_id: int,
    text: str,
    entities: list,
    media=None,
) -> None:
    """
    Отредактировать текст/подпись сообщения с сохранением entities.

    Аналог pyrogram_fork/edit_media_message.py:EditMessageMedia.edit_message_media.
    Использует низкоуровневый EditMessageRequest.

    :param client: TelegramClient (userbot).
    :param chat_id: Чат с сообщением.
    :param msg_id: ID редактируемого сообщения.
    :param text: Новый текст/подпись.
    :param entities: Новые entities.
    :param media: InputMedia если нужно заменить медиа, иначе None.
    """
    peer = await client.get_input_entity(chat_id)

    await client(
        _EditMessageRequest(
            peer=peer,
            id=msg_id,
            message=text or "",
            entities=entities or [],
            media=media,
            no_webpage=True,
        )
    )
