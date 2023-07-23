from plugins.user.types import Operation


def default_log_asserts(caplog, operation: Operation):
    assert 'Добавлена блокировка all для чата 0 0' in caplog.text
    assert f'Источник 0 {operation.value} сообщение 0' in caplog.text
    assert 'Снята блокировка all для чата 0 0' in caplog.text
