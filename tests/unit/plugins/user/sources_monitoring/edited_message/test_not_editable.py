import logging
from unittest.mock import MagicMock, Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message

from .utils import (
    default_edited_message_log_asserts,
    setup_get_history_obj,
    setup_json_loads,
)


@pytest.mark.asyncio
async def test_not_editable_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_get_history_obj(
        mocker, return_value=MagicMock(category_message_rewritten=False)
    )

    setup_json_loads(mocker)

    await edited_message.edited_message(client=client, message=message)

    assert (
        "Источник 0 изменил сообщение 0, оно не может быть изменено в категории, потому"
        " что было переслано и не перепечатывалось" in caplog.text
    )
    default_edited_message_log_asserts(caplog=caplog)
