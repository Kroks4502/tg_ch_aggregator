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
    default_setup,
    history_new_message_asserts,
    history_with_category_asserts,
    setup_filtered,
    setup_history_save_and_get_history_objs,
    setup_repeated,
    setup_source,
)


@pytest.mark.asyncio
async def test_text_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client,
    input_message,
):
    caplog.set_level(logging.DEBUG)

    default_setup(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    setup_repeated(mocker, None)
    setup_filtered(mocker, None)

    ###

    input_attrs = []

    mock_category_msg = MagicMock()

    def se_new_one_message(message: Message, source: Source):
        input_attrs.append(message)
        input_attrs.append(source)
        return mock_category_msg

    mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_one_message",
        side_effect=se_new_one_message,
    )

    mock_history_save, history_objs = setup_history_save_and_get_history_objs(mocker)

    ###
    await new_message(client=client, message=input_message)
    ###

    output_message, output_source = input_attrs

    assert output_message is input_message
    assert output_source is mock_source

    history = history_objs[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=input_message,
    )
    history_with_category_asserts(
        history=history,
        input_source=mock_source,
        mock_category_msg=mock_category_msg,
    )
    assert len(history.data) == 1

    assert mock_history_save.call_count == 1

    assert len(blocking_messages.get(key=input_message.chat.id)) == 0

    assert 'Источник 0 отправил сообщение 0, оно отправлено в категорию' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
