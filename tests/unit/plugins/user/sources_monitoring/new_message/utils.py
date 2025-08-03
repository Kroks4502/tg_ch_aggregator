from unittest.mock import MagicMock, Mock

from pytest_mock import MockerFixture

from models import MessageHistory
from plugins.user.types import Operation

from ..utils import (
    default_log_asserts,
    set_return_value,
    setup_json_loads,
)

ALL = [
    "default_new_message_log_asserts",
    "setup_repeated",
    "setup_filtered",
    "setup_source",
    "setup_history_save",
    "history_new_message_asserts",
    "history_with_category_asserts",
    setup_json_loads,
]


def default_new_message_log_asserts(caplog) -> None:
    default_log_asserts(caplog=caplog, operation=Operation.NEW)


def setup_repeated(mocker: MockerFixture, return_value=...) -> MagicMock:
    mock = mocker.patch(
        "plugins.user.sources_monitoring.new_message.get_repeated_history_id_or_none"
    )
    set_return_value(mock, return_value)
    return mock


def setup_filtered(mocker: MockerFixture, return_value=...) -> MagicMock:
    mock = mocker.patch(
        "plugins.user.sources_monitoring.new_message.get_filter_id_or_none"
    )
    set_return_value(mock, return_value)
    return mock


def setup_source(mocker: MockerFixture, return_value=...) -> MagicMock:
    mock = mocker.patch("plugins.user.sources_monitoring.new_message.Source")
    set_return_value(mock, return_value)
    return mock


def setup_history_save(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "plugins.user.sources_monitoring.new_message.MessageHistory.save",
        autospec=True,
    )


def history_new_message_asserts(
    history: MessageHistory,
    input_source: MagicMock,
    input_message: Mock,
    repeat_history_id: int = None,
    filter_id: int = None,
) -> None:
    assert history.source_id is input_source.id
    assert history.source_message_id is input_message.id
    assert history.source_media_group_id is input_message.media_group_id

    assert history.source_forward_from_chat_id is input_message.forward_from_chat.id
    assert (
        history.source_forward_from_message_id is input_message.forward_from_message_id
    )

    assert history.category_id is input_source.category_id
    assert history.repeat_history_id is repeat_history_id
    assert history.filter_id is filter_id
    assert history.created_at is input_message.date

    assert "first_message" in history.data
    assert "source" in history.data["first_message"]


def history_with_category_asserts(
    history: MessageHistory,
    input_source: MagicMock,
    mock_category_msg: MagicMock,
) -> None:
    assert history.category_message_rewritten is input_source.is_rewrite
    assert history.category_message_id is mock_category_msg.id
    assert history.category_media_group_id is mock_category_msg.media_group_id
    assert "category" in history.data["first_message"]
