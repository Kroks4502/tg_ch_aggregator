import logging
from unittest.mock import MagicMock, Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.common import blocking_messages
from plugins.user.sources_monitoring.new_message import new_message
from tests.new_message.utils import (
    default_new_message_log_asserts,
    history_new_message_asserts,
    history_with_category_asserts,
    setup_filtered,
    setup_history_save,
    setup_repeated,
    setup_source,
)
from tests.utils import setup_json_loads


@pytest.mark.asyncio
async def test_media_group_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    media_group_message: Mock,
):
    caplog.set_level(logging.DEBUG)

    setup_json_loads(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    mock_repeated = setup_repeated(mocker, None)
    mock_filtered = setup_filtered(mocker, None)

    mock_new_media_group_messages = mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_media_group_messages",
        return_value=[MagicMock()],
    )

    mock_history_save = setup_history_save(mocker)

    ###
    await new_message(client=client, message=media_group_message)
    ###

    mock_new_media_group_messages.assert_called_once()
    media_group_message.get_media_group.assert_called_once()
    mock_repeated.assert_called_once()
    mock_filtered.assert_called_once()
    mock_history_save.assert_called_once()
    client.read_chat_history.assert_called_once()

    assert media_group_message in mock_new_media_group_messages.call_args.kwargs["messages"]
    assert mock_new_media_group_messages.call_args.kwargs["source"] is mock_source

    history = mock_history_save.call_args.args[0]
    history_new_message_asserts(
        history=history,
        input_source=mock_source,
        input_message=media_group_message,
    )
    history_with_category_asserts(
        history=history,
        input_source=mock_source,
        mock_category_msg=mock_new_media_group_messages.return_value[0],
    )
    assert len(history.data) == 1

    assert len(blocking_messages.get(key=media_group_message.chat.id)) == 0

    assert 'Источник 0 отправил сообщение 0 в составе медиа группы 0, сообщения отправлены в категорию' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
