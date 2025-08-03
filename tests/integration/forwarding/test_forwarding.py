import asyncio
import time

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

from .common import (
    MESSAGE_TIMEOUT,
    create_fingerprint,
    last_update_id,
    wait_for_edited_message,
    wait_for_message,
)


@pytest.mark.asyncio(loop_scope="session")
async def test_plain_text(
    bot: Bot,
    source_channel: int,
    aggregator_channel: int,
) -> None:
    offset = await last_update_id(bot)
    fingerprint = create_fingerprint()

    await bot.send_message(source_channel, fingerprint)
    forwarded = await wait_for_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.text is not None and fingerprint in m.text,
    )

    assert forwarded.text is not None
    assert fingerprint in forwarded.text


@pytest.mark.asyncio(loop_scope="session")
async def test_edit_message_forward(
    bot: Bot,
    source_channel: int,
    aggregator_channel: int,
) -> None:
    offset = await last_update_id(bot)
    fingerprint = create_fingerprint()

    new_message = await bot.send_message(source_channel, fingerprint)
    forwarded = await wait_for_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.text is not None and fingerprint in m.text,
    )

    assert forwarded.text is not None
    assert fingerprint in forwarded.text

    edited = f"edited {fingerprint}"
    await bot.edit_message_text(
        chat_id=source_channel,
        message_id=new_message.message_id,
        text=edited,
    )
    edited_msg = await wait_for_edited_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.text is not None and fingerprint in m.text,
    )

    assert edited_msg.text is not None
    assert fingerprint in edited_msg.text


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_message_forward(
    bot: Bot,
    source_channel: int,
    aggregator_channel: int,
) -> None:
    offset = await last_update_id(bot)
    fingerprint = create_fingerprint()

    new_message = await bot.send_message(source_channel, fingerprint)
    forwarded = await wait_for_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.text is not None and fingerprint in m.text,
    )

    assert forwarded.text is not None
    assert fingerprint in forwarded.text

    await bot.delete_message(source_channel, new_message.message_id)

    deadline = time.time() + MESSAGE_TIMEOUT
    while time.time() < deadline:
        try:
            await bot.edit_message_text(
                text="for delete",
                chat_id=source_channel,
                message_id=forwarded.message_id,
            )
        except TelegramBadRequest as e:
            if "message to edit not found" in str(e).lower():
                break
        else:
            await asyncio.sleep(2)
    else:
        pytest.fail("forwarded message was not deleted")
