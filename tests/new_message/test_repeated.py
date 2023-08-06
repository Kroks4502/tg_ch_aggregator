import logging
from unittest.mock import Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.common import blocking_messages
from plugins.user.sources_monitoring.new_message import new_message
from plugins.user.types import Operation
from tests.new_message.utils import (
    default_new_message_log_asserts,
    history_new_message_asserts,
    setup_filtered,
    setup_history_save,
    setup_repeated,
    setup_source,
)
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_repeated_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_json_loads(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()

    repeat_history_id = 1
    setup_repeated(mocker, repeat_history_id)
    setup_filtered(mocker, None)

    mock_history_save = setup_history_save(mocker)

    ###
    await new_message(client=client, message=message)
    ###

    history = mock_history_save.call_args.args[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=message,
        repeat_history_id=repeat_history_id,
    )
    assert "exception" in history.data[-1]
    exception = history.data[-1]["exception"]
    assert exception["name"] == "MessageRepeatedError"
    assert exception["text"] == "Источник 0 отправил сообщение 0, оно уже опубликовано в категории."
    assert exception["operation"] == Operation.NEW.name
    assert len(history.data) == 1

    assert mock_history_save.call_count == 1

    assert len(blocking_messages.get(key=message.chat.id)) == 0

    assert 'Источник 0 отправил сообщение 0, оно уже опубликовано в категории.' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
