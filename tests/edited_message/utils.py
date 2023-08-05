from pytest_mock import MockerFixture

from plugins.user.types import Operation
from tests.utils import default_log_asserts, set_return_value


def default_edited_message_log_asserts(caplog):
    default_log_asserts(caplog=caplog, operation=Operation.EDIT)


def setup_filtered(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.edited_message.get_filter_id_or_none")
    set_return_value(mock, return_value)
    return mock


def setup_source(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.edited_message.Source")
    set_return_value(mock, return_value)
    return mock
