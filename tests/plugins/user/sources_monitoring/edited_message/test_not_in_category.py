import logging
from unittest.mock import MagicMock, Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.plugins.user.sources_monitoring.edited_message.utils import (
    default_edited_message_log_asserts,
    setup_get_history_obj,
)
from tests.plugins.user.sources_monitoring.utils import setup_json_loads


@pytest.mark.asyncio
async def test_not_in_category_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_get_history_obj(mocker, return_value=MagicMock(category_message_id=None))

    setup_json_loads(mocker)

    await edited_message.edited_message(client=client, message=message)

    assert (
        "Источник 0 изменил сообщение 0, оно не публиковалось в категории"
        in caplog.text
    )
    default_edited_message_log_asserts(caplog=caplog)
