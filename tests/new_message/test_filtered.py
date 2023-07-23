import logging

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock import MockerFixture

from plugins.user.sources_monitoring.new_message import new_message
from tests.new_message.utils import (
    default_new_message_log_asserts,
    default_setup,
    history_new_message_asserts,
    setup_filtered,
    setup_history_save_and_get_history_objs,
    setup_repeated,
    setup_source,
)


@pytest.mark.asyncio
async def test_filtered_message(
    mocker: MockerFixture,
    caplog: LogCaptureFixture,
    client,
    input_message,
):
    caplog.set_level(logging.DEBUG)

    default_setup(mocker)
    input_source = setup_source(mocker)
    input_source = input_source.get()

    setup_repeated(mocker, None)
    filter_id = 1
    setup_filtered(mocker, filter_id)

    history_objs = setup_history_save_and_get_history_objs(mocker)

    ###
    await new_message(client=client, message=input_message)
    ###

    history = history_objs[0]
    history_new_message_asserts(
        history=history,
        input_source=input_source,
        input_message=input_message,
        filter_id=filter_id,
    )
    assert len(history.data) == 1

    assert 'Источник 0 отправил сообщение 0, оно было отфильтровано.' in caplog.text
    default_new_message_log_asserts(caplog=caplog)
