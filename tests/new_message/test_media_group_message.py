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
async def test_media_group_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client,
    media_group_message,
):
    caplog.set_level(logging.DEBUG)

    default_setup(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    mock_repeated = setup_repeated(mocker, None)
    mock_filtered = setup_filtered(mocker, None)

    ###

    input_attrs = dict()

    mock_category_msg = MagicMock()

    def se_new_media_group_messages(client, messages: list[Message], source: Source):
        input_attrs["messages"] = messages
        input_attrs["source"] = source
        return [mock_category_msg]

    mock_new_media_group_messages = mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_media_group_messages",
        side_effect=se_new_media_group_messages,
    )

    mock_history_save, history_objs = setup_history_save_and_get_history_objs(mocker)

    ###
    await new_message(client=client, message=media_group_message)
    ###

    assert mock_new_media_group_messages.call_count == 1
    assert media_group_message.get_media_group.call_count == 1
    assert mock_repeated.call_count == 1
    assert mock_filtered.call_count == 1
    assert mock_history_save.call_count == 1
    assert client.read_chat_history.call_count == 1

    output_messages, output_source = input_attrs.values()

    assert media_group_message in output_messages
    assert output_source is mock_source

    history = history_objs[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=media_group_message,
    )
    history_with_category_asserts(
        history=history,
        input_source=mock_source,
        mock_category_msg=mock_category_msg,
    )
    assert len(history.data) == 1

    assert len(blocking_messages.get(key=media_group_message.chat.id)) == 0

    assert 'Источник 0 отправил сообщение 0 в составе медиа группы 0, сообщения отправлены в категорию' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
