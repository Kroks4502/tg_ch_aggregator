import logging
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.edited_message.utils import (
    default_edited_message_log_asserts,
    setup_get_history_obj,
)


@pytest.mark.asyncio
async def test_not_in_history_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_get_history_obj(mocker, return_value=None)

    message.edit_date = 0
    message.date = 0
    await edited_message.edited_message(client=client, message=message)

    assert 'Источник 0 изменил сообщение 0, его нет в истории' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
