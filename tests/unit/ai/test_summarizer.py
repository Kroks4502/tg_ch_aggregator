import os

os.environ.setdefault("OPENAI_API_KEY", "test")

import pytest  # noqa: E402

from utils.ai import summarize_messages  # noqa: E402


class _DummyResponse:
    def __init__(self, parsed):
        self.choices = [
            type("Choice", (), {"message": type("Message", (), {"parsed": parsed})})
        ]


@pytest.mark.asyncio
async def test_summarize_messages_returns_structured_list(monkeypatch):
    async def fake_create(*args, **kwargs):
        return _DummyResponse([{"text": "summary", "links": ["l1", "l2"]}])

    class DummyClient:
        class Chat:
            class Completions:
                create = fake_create

            completions = Completions()

        chat = Chat()

    dummy = DummyClient()
    monkeypatch.setitem(summarize_messages.__globals__, "client", dummy)

    messages = [("text1", "l1"), ("text2", "l2")]
    result = await summarize_messages(messages)

    assert result == [{"text": "summary", "links": ["l1", "l2"]}]


@pytest.mark.asyncio
async def test_summarize_messages_empty(monkeypatch):
    class DummyClient:
        class Chat:
            class Completions:
                async def create(self, *args, **kwargs):
                    raise AssertionError("create should not be called")

            completions = Completions()

        chat = Chat()

    dummy = DummyClient()
    monkeypatch.setitem(summarize_messages.__globals__, "client", dummy)

    result = await summarize_messages([])

    assert result == []
