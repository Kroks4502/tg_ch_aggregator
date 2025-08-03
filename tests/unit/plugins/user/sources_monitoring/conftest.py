from unittest.mock import AsyncMock, Mock

import pytest
from pyrogram import enums

import settings


@pytest.fixture(autouse=True)
def configure():
    settings.DUMP_MESSAGE_MODE = False


@pytest.fixture()
def client():
    mock_client = Mock(name="client")
    mock_client.read_chat_history = AsyncMock()
    mock_client.read_chat_history.return_value = True
    return mock_client


@pytest.fixture()
def chat():
    return Mock(
        id=0,
        type=enums.ChatType.CHANNEL,
    )


@pytest.fixture()
def message(chat: Mock):
    return Mock(
        name="message",
        id=0,
        chat=chat,
        media_group_id=None,
    )


@pytest.fixture()
def media_message(chat: Mock):
    return Mock(
        name="media_message",
        id=0,
        chat=chat,
        media_group_id=None,
        text=None,
    )


@pytest.fixture()
def media_group_message(chat: Mock):
    message = Mock(
        name="media_group_message",
        id=0,
        chat=chat,
        media_group_id="0",
        get_media_group=AsyncMock(),
        text=None,
    )
    message.get_media_group.return_value = [message]
    return message
