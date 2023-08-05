import logging
from unittest.mock import AsyncMock, Mock

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
async def test_edited_text_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    mocker.patch("plugins.user.sources_monitoring.edited_message.MessageHistory.get_or_none")
    setup_source(mocker)
    setup_filtered(mocker, return_value=None)

    mocker.patch("plugins.user.sources_monitoring.edited_message.cleanup_message")
    mocker.patch("plugins.user.sources_monitoring.edited_message.add_header")
    mocker.patch("plugins.user.sources_monitoring.edited_message.cut_long_message")

    setup_json_loads(mocker)

    client.edit_message_text = AsyncMock()

    await edited_message.edited_message(client=client, message=message)

    assert 'Источник 0 изменил сообщение 0, оно изменено в категории' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
