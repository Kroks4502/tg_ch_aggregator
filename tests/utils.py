from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from plugins.user.types import Operation


def default_log_asserts(caplog, operation: Operation):
    assert 'Добавлена блокировка all для чата 0 0' in caplog.text
    assert f'Источник 0 {operation.value} сообщение 0' in caplog.text
    assert 'Снята блокировка all для чата 0 0' in caplog.text


def set_return_value(mock: MagicMock, return_value):
    if return_value is not ...:
        mock.return_value = return_value


def setup_source(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("models.Source")
    set_return_value(mock, return_value)
    return mock


def setup_filtered(mocker: MockerFixture, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.common.get_filter_id_or_none")
    set_return_value(mock, return_value)
    return mock


def setup_json_loads(mocker, return_value=...):
    mock = mocker.patch("plugins.user.sources_monitoring.new_message.json.loads")
    set_return_value(mock, return_value)
    return mock
