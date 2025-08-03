import asyncio
import time
from typing import Callable

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message


async def _last_update_id(bot: Bot) -> int:
    updates = await bot.get_updates(timeout=0, allowed_updates=["channel_post"])
    return updates[-1].update_id + 1 if updates else 0


async def _wait_for_message(
    bot: Bot,
    channel_id: int,
    offset: int,
    check: Callable[[Message], bool],
    timeout: float = 20.0,
) -> Message:
    deadline = time.time() + timeout
    while time.time() < deadline:
        updates = await bot.get_updates(
            offset=offset, timeout=2, allowed_updates=["channel_post"]
        )
        for upd in updates:
            offset = upd.update_id + 1
            msg = upd.channel_post
            if msg and msg.chat.id == channel_id and check(msg):
                return msg
    raise AssertionError("message was not forwarded to aggregator channel")


async def _wait_for_edited_message(
    bot: Bot,
    channel_id: int,
    offset: int,
    check: Callable[[Message], bool],
    timeout: float = 20.0,
) -> Message:
    deadline = time.time() + timeout
    while time.time() < deadline:
        updates = await bot.get_updates(
            offset=offset, timeout=2, allowed_updates=["edited_channel_post"]
        )
        for upd in updates:
            offset = upd.update_id + 1
            msg = upd.edited_channel_post
            if msg and msg.chat.id == channel_id and check(msg):
                return msg
    raise AssertionError("edited message was not received in aggregator channel")


@pytest.mark.asyncio
async def test_plain_text_forward(
    bot: Bot, source_channel: int, aggregator_channel: int
) -> None:
    offset = await _last_update_id(bot)
    text = f"plain text {time.time()}"
    await bot.send_message(source_channel, text)
    forwarded = await _wait_for_message(
        bot, aggregator_channel, offset, lambda m: m.text == text
    )
    assert forwarded.text == text


@pytest.mark.asyncio
async def test_formatted_text_forward(
    bot: Bot, source_channel: int, aggregator_channel: int
) -> None:
    offset = await _last_update_id(bot)
    html = "<b>bold</b> <i>italic</i>"
    expected = "bold italic"
    await bot.send_message(source_channel, html, parse_mode="HTML")
    forwarded = await _wait_for_message(
        bot, aggregator_channel, offset, lambda m: m.text == expected
    )
    types = {e.type for e in (forwarded.entities or [])}
    assert {"bold", "italic"}.issubset(types)


@pytest.mark.asyncio
async def test_photo_with_caption_forward(
    bot: Bot, source_channel: int, aggregator_channel: int
) -> None:
    offset = await _last_update_id(bot)
    caption = f"photo caption {time.time()}"
    await bot.send_photo(
        source_channel,
        photo="https://picsum.photos/200/300",
        caption=caption,
    )
    forwarded = await _wait_for_message(
        bot, aggregator_channel, offset, lambda m: m.caption == caption
    )
    assert forwarded.photo
    assert forwarded.caption == caption


@pytest.mark.asyncio
async def test_forwarded_message_forward(
    bot: Bot, source_channel: int, aggregator_channel: int,
) -> None:
    offset = await _last_update_id(bot)
    original_text = f"forwarded {time.time()}"
    original_msg = await bot.send_message(aggregator_channel, original_text)
    await bot.forward_message(source_channel, aggregator_channel, original_msg.message_id)
    forwarded = await _wait_for_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: (
            m.forward_from_chat
            and m.forward_from_chat.id == aggregator_channel
            and m.text == original_text
        ),
    )
    assert forwarded.forward_from_chat
    assert forwarded.forward_from_chat.id == aggregator_channel
    assert forwarded.text == original_text


@pytest.mark.asyncio
async def test_forwarded_message_rewrite(
    bot: Bot,
    aggregator_channel: int,
    rewrite_source_channel: int,
    rewrite_aggregator_channel: int,
) -> None:
    offset = await _last_update_id(bot)
    original_text = f"rewrite forwarded {time.time()}"
    origin_msg = await bot.send_message(aggregator_channel, original_text)
    await bot.forward_message(
        rewrite_source_channel, aggregator_channel, origin_msg.message_id
    )
    forwarded = await _wait_for_message(
        bot,
        rewrite_aggregator_channel,
        offset,
        lambda m: (
            m.message_id != origin_msg.message_id
            and m.forward_from_chat is None
            and original_text in (m.text or "")
        ),
    )
    assert forwarded.forward_from_chat is None
    assert original_text in (forwarded.text or "")


@pytest.mark.asyncio
async def test_edit_message_forward(
    bot: Bot, source_channel: int, aggregator_channel: int
) -> None:
    offset = await _last_update_id(bot)
    text = f"to edit {time.time()}"
    msg = await bot.send_message(source_channel, text)
    forwarded = await _wait_for_message(
        bot, aggregator_channel, offset, lambda m: m.text == text
    )
    offset = await _last_update_id(bot)
    edited = f"edited {time.time()}"
    await bot.edit_message_text(
        chat_id=source_channel, message_id=msg.message_id, text=edited
    )
    edited_msg = await _wait_for_edited_message(
        bot,
        aggregator_channel,
        offset,
        lambda m: m.message_id == forwarded.message_id and m.text == edited,
    )
    assert edited_msg.text == edited


@pytest.mark.asyncio
async def test_delete_message_forward(
    bot: Bot, source_channel: int, aggregator_channel: int
) -> None:
    offset = await _last_update_id(bot)
    text = f"to delete {time.time()}"
    msg = await bot.send_message(source_channel, text)
    forwarded = await _wait_for_message(
        bot, aggregator_channel, offset, lambda m: m.text == text
    )
    await bot.delete_message(source_channel, msg.message_id)
    deadline = time.time() + 20
    while time.time() < deadline:
        try:
            tmp = await bot.forward_message(
                source_channel, aggregator_channel, forwarded.message_id
            )
        except TelegramBadRequest as e:
            if "message to forward not found" in str(e).lower():
                break
        else:
            await bot.delete_message(source_channel, tmp.message_id)
            await asyncio.sleep(1)
    else:
        pytest.fail("forwarded message was not deleted")
