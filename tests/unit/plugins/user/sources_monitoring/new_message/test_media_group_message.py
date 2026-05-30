import logging
from unittest.mock import MagicMock, Mock

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.common import blocking_messages
from plugins.user.sources_monitoring.new_message import handle_new_messages

from .utils import (
    default_new_message_log_asserts,
    history_new_message_asserts,
    history_with_category_asserts,
    setup_check_regex_alert,
    setup_filtered,
    setup_history_save,
    setup_json_loads,
    setup_repeated,
    setup_source,
)


@pytest.mark.asyncio
async def test_media_group_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    media_group_message: Mock,
):
    """
    Тест обработки медиа-группы через handle_new_messages.
    В Telethon-версии AlbumCollector собирает все сообщения альбома,
    затем вызывает handle_new_messages([msg1, msg2, ...]).
    """
    caplog.set_level(logging.DEBUG)

    setup_json_loads(mocker)
    mock_source = setup_source(mocker)
    mock_source = mock_source.get()
    mock_repeated = setup_repeated(mocker, None)
    mock_filtered = setup_filtered(mocker, None)
    setup_check_regex_alert(mocker)

    mock_new_media_group_messages = mocker.patch(
        "plugins.user.sources_monitoring.new_message.new_media_group_messages",
        return_value=[MagicMock()],
    )

    mock_history_save = setup_history_save(mocker)

    # В Telethon-архитектуре handle_new_messages вызывается с полным списком сообщений альбома
    ###
    await handle_new_messages(client=client, source_messages=[media_group_message, media_group_message])
    ###

    # Telethon: new_media_group_messages(client, messages, source) — позиционно
    mock_new_media_group_messages.assert_called_once_with(
        client,
        [media_group_message, media_group_message],
        mock_source,
    )
    mock_repeated.assert_called()
    mock_filtered.assert_called()
    mock_history_save.assert_called()
    # Telethon: send_read_acknowledge заменяет read_chat_history
    client.send_read_acknowledge.assert_called_once()

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

    assert len(blocking_messages.get(key=media_group_message.chat.id)) == 0

    assert (
        "Источник 0 отправил сообщение 0 (album=True)" in caplog.text
    )
    default_new_message_log_asserts(caplog=caplog)
