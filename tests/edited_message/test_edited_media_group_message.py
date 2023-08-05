import logging
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message
from tests.edited_message.utils import (
    default_edited_message_log_asserts,
    setup_filtered,
    setup_get_history_obj,
    setup_source,
)
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_edited_media_group_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    media_group_message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_get_history_obj(mocker)
    setup_source(mocker)
    setup_filtered(mocker, return_value=None)

    mocker.patch("plugins.user.sources_monitoring.edited_message.cleanup_message")
    mocker.patch("plugins.user.sources_monitoring.edited_message.add_header")
    mocker.patch("plugins.user.sources_monitoring.edited_message.cut_long_message")

    mocker.patch("plugins.user.sources_monitoring.edited_message.EditMessageMedia.edit_message_media")
    mocker.patch("plugins.user.sources_monitoring.edited_message.get_input_media")

    setup_json_loads(mocker)

    await edited_message.edited_message(client=client, message=media_group_message)

    assert 'Источник 0 изменил сообщение 0, оно изменено в категории' in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
