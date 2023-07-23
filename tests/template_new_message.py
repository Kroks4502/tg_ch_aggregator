import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.new_message import new_message


@pytest.mark.asyncio
async def base_test_new_regular_message(mocker: MockerFixture, caplog: LogCaptureFixture, client, regular_message):
    caplog.set_level(logging.DEBUG)

    mocker.patch("plugins.user.sources_monitoring.new_message.Source")
    mocker.patch("plugins.user.sources_monitoring.new_message.get_repeated_history_id_or_none")
    mocker.patch("plugins.user.sources_monitoring.new_message.get_filter_id_or_none")
    mocker.patch("plugins.user.sources_monitoring.new_message.json.loads")
    mocker.patch("plugins.user.sources_monitoring.new_message.MessageHistory.save")
    mocker.patch("plugins.user.sources_monitoring.new_message.new_one_message")
    mocker.patch("plugins.user.sources_monitoring.new_message.new_media_group_messages")
    mocker.patch("plugins.user.sources_monitoring.new_message.send_error_to_admins")

    await new_message(client=client, message=regular_message)

    assert 'Источник 0 отправил сообщение 0' in caplog.text
    assert 'Добавлена блокировка all для чата 0 0' in caplog.text
    assert 'Источник 0 отправил сообщение 0, оно уже опубликовано в категории.' in caplog.text
    # assert 'Источник 0 отправил сообщение 0, оно было отфильтровано.' in caplog.text
    assert 'Снята блокировка all для чата 0 0' in caplog.text
