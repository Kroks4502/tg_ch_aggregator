import logging
from unittest.mock import MagicMock

import pytest
from _pytest.logging import LogCaptureFixture
from pyrogram.types import Message
from pytest_mock import MockerFixture

from models import Source
from plugins.user.sources_monitoring.common import blocking_messages
from plugins.user.sources_monitoring.new_message import new_message
from tests.new_message.utils import (
    default_new_message_log_asserts,
    history_new_message_asserts,
    history_with_category_asserts,
    setup_filtered,
    setup_history_save_and_get_history_objs,
    setup_repeated,
    setup_source,
)
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_one_new_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client,
    message,
):
    caplog.set_level(logging.DEBUG)

    setup_json_loads(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    mock_repeated = setup_repeated(mocker, None)
    mock_filtered = setup_filtered(mocker, None)

    ###

    input_attrs = []

    mock_category_msg = MagicMock()

    def se_new_one_message(message: Message, source: Source):
        input_attrs.append(message)
        input_attrs.append(source)
        return mock_category_msg

    mock_new_one_message = mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_one_message",
        side_effect=se_new_one_message,
    )

    mock_history_save, history_objs = setup_history_save_and_get_history_objs(mocker)

    ###
    await new_message(client=client, message=message)
    ###

    assert mock_new_one_message.call_count == 1
    assert mock_repeated.call_count == 1
    assert mock_filtered.call_count == 1
    assert mock_history_save.call_count == 1
    assert client.read_chat_history.call_count == 1

    output_message, output_source = input_attrs

    assert output_message is message
    assert output_source is mock_source

    history = history_objs[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=message,
    )
    history_with_category_asserts(
        history=history,
        input_source=mock_source,
        mock_category_msg=mock_category_msg,
    )
    assert len(history.data) == 1

    assert len(blocking_messages.get(key=message.chat.id)) == 0

    assert 'Источник 0 отправил сообщение 0, оно отправлено в категорию' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
