import os
import pytest
from aiogram import Bot

pytest_plugins = ("pytest_asyncio",)


def _env_or_skip(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"environment variable {name} is not set")
    return value


@pytest.fixture(scope="session")
def bot_token() -> str:
    return _env_or_skip("TG_TEST_BOT_TOKEN")


@pytest.fixture(scope="session")
def source_channel() -> int:
    return int(_env_or_skip("TG_SOURCE_CHANNEL_ID"))


@pytest.fixture(scope="session")
def aggregator_channel() -> int:
    return int(_env_or_skip("TG_AGGREGATOR_CHANNEL_ID"))


@pytest.fixture(scope="session")
def rewrite_source_channel() -> int:
    return int(_env_or_skip("TG_REWRITE_SOURCE_CHANNEL_ID"))


@pytest.fixture(scope="session")
def rewrite_aggregator_channel() -> int:
    return int(_env_or_skip("TG_REWRITE_AGGREGATOR_CHANNEL_ID"))


@pytest.fixture(scope="session")
async def bot(bot_token: str) -> Bot:
    bot = Bot(token=bot_token)
    yield bot
    await bot.session.close()
