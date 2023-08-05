import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.edited_message.utils import default_edited_message_log_asserts


@pytest.mark.asyncio
async def test_not_in_history_message(mocker: MockerFixture, caplog: LogCaptureFixture, client, message):
    caplog.set_level(logging.DEBUG)

    mocker.patch(
        "plugins.user.sources_monitoring.edited_message.MessageHistory.get_or_none",
        return_value=None,
    )

    message.edit_date = 0
    message.date = 0
    await edited_message.edited_message(client=client, message=message)

    assert 'Источник 0 изменил сообщение 0, его нет в истории' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
