import os

import pytest

if not os.getenv("OPENAI_API_KEY"):
    pytest.skip("OPENAI_API_KEY is not set", allow_module_level=True)

from utils.ai import summarize_messages


@pytest.mark.asyncio
async def test_summarize_messages_integration():
    messages = [
        ("first", "https://example.com/1"),
        ("second", "https://example.com/2"),
    ]

    result = await summarize_messages(messages)

    assert isinstance(result, list)
    assert all("text" in item and "links" in item for item in result)
