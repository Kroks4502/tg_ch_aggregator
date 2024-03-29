import logging
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.common import blocking_messages
from plugins.user.sources_monitoring.new_message import new_message
from tests.plugins.user.sources_monitoring.new_message.utils import (
    default_new_message_log_asserts,
    history_new_message_asserts,
    history_with_category_asserts,
    setup_filtered,
    setup_history_save,
    setup_repeated,
    setup_source,
)
from tests.plugins.user.sources_monitoring.utils import setup_json_loads


@pytest.mark.asyncio
async def test_new_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_json_loads(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    mock_repeated = setup_repeated(mocker, None)
    mock_filtered = setup_filtered(mocker, None)

    mock_new_one_message = mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_one_message"
    )

    mock_history_save = setup_history_save(mocker)

    ###
    await new_message(client=client, message=message)
    ###

    mock_new_one_message.assert_called_once_with(message=message, source=mock_source)
    mock_repeated.assert_called_once()
    mock_filtered.assert_called_once()
    mock_history_save.assert_called_once()
    client.read_chat_history.assert_called_once()

    history = mock_history_save.call_args.args[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=message,
    )
    history_with_category_asserts(
        history=history,
        input_source=mock_source,
        mock_category_msg=mock_new_one_message.return_value,
    )
    assert len(history.data) == 1

    assert len(blocking_messages.get(key=message.chat.id)) == 0

    assert "Источник 0 отправил сообщение 0, оно отправлено в категорию" in caplog.text
    default_new_message_log_asserts(caplog=caplog)
