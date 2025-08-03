import pytest
from aiogram import Bot

from .common import (
    aggregator_header_title,
    aggregator_message_link,
    create_fingerprint,
    last_update_id,
    wait_for_message,
)


@pytest.mark.asyncio(loop_scope="session")
async def test_aggregator_message_header(
    bot: Bot,
    source_channel: int,
    aggregator_channel: int,
) -> None:
    offset = await last_update_id(bot)
    text = create_fingerprint()
    message = await bot.send_message(source_channel, text)

    header = await aggregator_header_title(bot, source_channel)
    link = aggregator_message_link(message)

    forwarded = await wait_for_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.text is not None and text in m.text,
    )

    assert forwarded.text == f"{header}\n{text}"

    assert forwarded.entities is not None
    assert len(forwarded.entities) == 2

    assert forwarded.entities[0].type == "text_link"
    assert forwarded.entities[0].offset == 0
    assert forwarded.entities[0].length == len(header)
    assert forwarded.entities[0].url == link

    assert forwarded.entities[1].type == "bold"
    assert forwarded.entities[1].offset == 0
    assert forwarded.entities[1].length == len(header)
