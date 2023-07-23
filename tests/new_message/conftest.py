from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture()
def one_message(message: Mock):
    message.media_group_id = None
    return message


@pytest.fixture()
def media_group_message(message: Mock):
    message.media_group_id = "0"
    message.get_media_group = AsyncMock(return_value=[message])
    return message
