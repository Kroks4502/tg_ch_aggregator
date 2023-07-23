from unittest.mock import Mock

import pytest


@pytest.fixture()
def one_message(message: Mock):
    message.media_group_id = None
    return message
