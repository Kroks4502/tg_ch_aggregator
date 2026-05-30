import logging
from unittest.mock import AsyncMock, Mock

import pytest
from _pytest.fixtures import FixtureRequest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring import edited_message

from .utils import (
    default_edited_message_log_asserts,
    setup_filtered,
    setup_get_history_obj,
    setup_json_loads,
    setup_source,
)


@pytest.mark.asyncio
@pytest.mark.parametrize("msg", ["message", "media_message", "media_group_message"])
async def test_edited_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client: Mock,
    msg: str,
    request: FixtureRequest,
):
    message = request.getfixturevalue(msg)

    caplog.set_level(logging.DEBUG)

    mock_get_history_obj = setup_get_history_obj(mocker)
    setup_source(mocker)
    setup_filtered(mocker, return_value=None)

    mocker.patch("plugins.user.sources_monitoring.edited_message.cleanup_message")
    mocker.patch("plugins.user.sources_monitoring.edited_message.add_header")
    mocker.patch("plugins.user.sources_monitoring.edited_message.cut_long_message")
    # Мокаем DB-запрос для медиа-группы
    mocker.patch(
        "plugins.user.sources_monitoring.edited_message._is_text_in_mediagroup",
        return_value=False,
    )

    # Telethon-версия: edit_message_with_entities заменяет EditMessageMedia + edit_message_text
    mock_edit = mocker.patch(
        "plugins.user.sources_monitoring.edited_message.edit_message_with_entities"
    )
    mocker.patch("plugins.user.sources_monitoring.edited_message._get_album_input_media")
    # get_messages нужен для получения category_message после edit
    client.get_messages = AsyncMock(return_value=[])

    setup_json_loads(mocker)

    ###
    await edited_message.edited_message(client=client, message=message)
    ###

    mock_edit.assert_called_once()
    mock_get_history_obj.assert_called_once_with(
        source_id=message.chat_id, source_message_id=message.id
    )
    mock_history_obj = mock_get_history_obj.return_value
    assert mock_history_obj.edited_at == message.edit_date
    mock_history_obj.save.assert_called_once()

    assert "Источник 0 изменил сообщение 0 → обновлено в категории" in caplog.text
    default_edited_message_log_asserts(caplog=caplog)
