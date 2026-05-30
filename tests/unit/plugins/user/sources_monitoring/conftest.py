from unittest.mock import AsyncMock, Mock

import pytest

import settings


@pytest.fixture(autouse=True)
def configure():
    settings.DUMP_MESSAGE_MODE = False


@pytest.fixture()
def client():
    mock_client = Mock(name="client")
    # Telethon: send_read_acknowledge (заменяет pyrogram's read_chat_history)
    mock_client.send_read_acknowledge = AsyncMock()
    return mock_client


@pytest.fixture()
def chat():
    return Mock(id=0)


@pytest.fixture()
def message(chat: Mock):
    return Mock(
        name="message",
        id=0,
        chat=chat,
        # Telethon атрибуты
        chat_id=0,
        grouped_id=None,     # Telethon (был media_group_id)
        media_group_id=None,  # оставлен для совместимости тестов
        media=None,
        date=None,
        edit_date=None,
        fwd_from=None,
        reply_to=None,
    )


@pytest.fixture()
def media_message(chat: Mock):
    return Mock(
        name="media_message",
        id=0,
        chat=chat,
        chat_id=0,
        grouped_id=None,
        media_group_id=None,
        media=Mock(),  # не None — значит медиа
        text=None,
        date=None,
        edit_date=None,
        fwd_from=None,
        reply_to=None,
    )


@pytest.fixture()
def media_group_message(chat: Mock):
    message = Mock(
        name="media_group_message",
        id=0,
        chat=chat,
        chat_id=0,
        grouped_id="0",       # Telethon
        media_group_id="0",   # оставлен для совместимости тестов
        media=Mock(),
        text=None,
        date=None,
        edit_date=None,
        fwd_from=None,
        reply_to=None,
    )
    return message
