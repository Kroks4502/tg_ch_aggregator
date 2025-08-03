import logging
from typing import Dict, Tuple

import pytest

_test_failed_incremental: Dict[str, Dict[Tuple[int, ...], str]] = {}


def pytest_runtest_makereport(item, call):
    if "incremental" in item.keywords:
        if call.excinfo is not None:
            cls_name = str(item.cls)
            parametrize_index = (
                tuple(item.callspec.indices.values())
                if hasattr(item, "callspec")
                else ()
            )
            test_name = item.originalname or item.name
            _test_failed_incremental.setdefault(cls_name, {}).setdefault(
                parametrize_index, test_name
            )


def pytest_runtest_setup(item):
    if "incremental" in item.keywords:
        cls_name = str(item.cls)
        if cls_name in _test_failed_incremental:
            parametrize_index = (
                tuple(item.callspec.indices.values())
                if hasattr(item, "callspec")
                else ()
            )
            test_name = _test_failed_incremental[cls_name].get(parametrize_index, None)
            if test_name is not None:
                pytest.xfail(f"previous test failed ({test_name})")


def pytest_configure(config):
    """Disable the loggers."""
    for name in config.getoption("--log-disable", default=[]):
        logger = logging.getLogger(name)
        logger.propagate = False

    # if not config.option.log_file:
    #     timestamp = datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")
    #     config.option.log_file = f"{settings.LOGS_DIR}/pytest_{timestamp}.log"
