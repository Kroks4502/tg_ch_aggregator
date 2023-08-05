import logging
from unittest.mock import AsyncMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.edited_message.utils import (
    default_edited_message_log_asserts,
    setup_filtered,
    setup_source,
)
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_filtered_message(mocker: MockerFixture, caplog: LogCaptureFixture, client, message):
    caplog.set_level(logging.DEBUG)

    mocker.patch("plugins.user.sources_monitoring.edited_message.MessageHistory.get_or_none")
    setup_source(mocker)
    setup_filtered(mocker)

    mocker.patch("plugins.user.sources_monitoring.edited_message.cleanup_message")
    mocker.patch("plugins.user.sources_monitoring.edited_message.add_header")
    mocker.patch("plugins.user.sources_monitoring.edited_message.cut_long_message")

    mocker.patch("plugins.user.sources_monitoring.edited_message.EditMessageMedia.edit_message_media")

    setup_json_loads(mocker)

    client.edit_message_text = AsyncMock()

    await edited_message.edited_message(client=client, message=message)

    assert 'Источник 0 изменил сообщение 0, оно было отфильтровано' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
