import logging
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.edited_message.utils import default_edited_message_log_asserts
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_not_in_category_message(mocker: MockerFixture, caplog: LogCaptureFixture, client, message):
    caplog.set_level(logging.DEBUG)

    mocker.patch(
        "plugins.user.sources_monitoring.edited_message.MessageHistory.get_or_none",
        return_value=MagicMock(category_message_id=None),
    )

    setup_json_loads(mocker)

    await edited_message.edited_message(client=client, message=message)

    assert 'Источник 0 изменил сообщение 0, оно не публиковалось в категории' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
