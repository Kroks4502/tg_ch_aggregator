from unittest.mock import MagicMock, Mock

from pytest_mock import MockerFixture

from models import MessageHistory
from plugins.user.types import Operation
from tests.utils import default_log_asserts, set_return_value


def default_new_message_log_asserts(caplog):
    default_log_asserts(caplog=caplog, operation=Operation.NEW)


def setup_repeated(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.new_message.get_repeated_history_id_or_none")
    set_return_value(mock, return_value)
    return mock


def setup_filtered(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.new_message.get_filter_id_or_none")
    set_return_value(mock, return_value)
    return mock


def setup_source(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.new_message.Source")
    set_return_value(mock, return_value)
    return mock


def setup_history_save_and_get_history_objs(mocker: MockerFixture) -> tuple[MagicMock, list[MessageHistory]]:
    history_objs = []

    def se_history_save(self):
        history_objs.append(self)
        return MagicMock("HistoryMock")

    mock = mocker.patch(
        "plugins.user.sources_monitoring.new_message.MessageHistory.save",
        side_effect=se_history_save,
        autospec=True,
    )
    return mock, history_objs


def history_new_message_asserts(
    history: MessageHistory,
    input_source: MagicMock,
    input_message: Mock,
    repeat_history_id: int = None,
    filter_id: int = None,
):
    assert history.source_id is input_source.id
    assert history.source_message_id is input_message.id
    assert history.source_media_group_id is input_message.media_group_id

    assert history.source_forward_from_chat_id is input_message.forward_from_chat.id
    assert history.source_forward_from_message_id is input_message.forward_from_message_id

    assert history.category_id is input_source.category_id
    assert history.repeat_history_id is repeat_history_id
    assert history.filter_id is filter_id
    assert history.created_at is input_message.date
    assert "source" in history.data[-1]


def history_with_category_asserts(
    history: MessageHistory,
    input_source: MagicMock,
    mock_category_msg: MagicMock,
):
    assert history.category_message_rewritten is input_source.is_rewrite
    assert history.category_message_id is mock_category_msg.id
    assert history.category_media_group_id is mock_category_msg.media_group_id
    assert "category" in history.data[-1]
