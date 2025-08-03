import time
import uuid
from typing import Callable

from aiogram import Bot
from aiogram.types import Message

from plugins.user.utils.rewriter.header import SRC_TEXT_TMPL

MESSAGE_TIMEOUT = 20.0


async def last_update_id(bot: Bot) -> int:
    updates = await bot.get_updates(timeout=0, allowed_updates=["channel_post"])
    return updates[-1].update_id + 1 if updates else 0


async def aggregator_header_title(bot: Bot, channel_id: int) -> str:
    """Получаем имя источника, чтобы посчитать смещение для сущностей."""
    channel_name = (await bot.get_chat(channel_id)).title
    return f"{SRC_TEXT_TMPL.format(channel_name)}\n"


def aggregator_message_link(message: Message) -> str:
    """Получаем ссылку на источник, чтобы посчитать смещение для сущностей."""
    chat_id = str(message.chat.id)[4:]
    return f"https://t.me/c/{chat_id}/{message.message_id}"


def create_fingerprint() -> str:
    return f"{str(uuid.uuid4())[:8]}-{time.time()}"


async def wait_for_message(
    bot: Bot,
    channel_id: int,
    offset: int,
    check: Callable[[Message], bool],
    timeout: float = MESSAGE_TIMEOUT,
) -> Message:
    deadline = time.time() + timeout
    while time.time() < deadline:
        updates = await bot.get_updates(
            offset=offset,
            timeout=2,
            allowed_updates=["channel_post"],
        )
        for upd in updates:
            offset = upd.update_id + 1
            msg = upd.channel_post
            if msg and msg.chat.id == channel_id and check(msg):
                return msg
    raise AssertionError("message was not forwarded to aggregator channel")


async def wait_for_edited_message(
    bot: Bot,
    channel_id: int,
    offset: int,
    check: Callable[[Message], bool],
    timeout: float = MESSAGE_TIMEOUT,
) -> Message:
    deadline = time.time() + timeout
    while time.time() < deadline:
        updates = await bot.get_updates(
            offset=offset,
            timeout=2,
            allowed_updates=["edited_channel_post"],
        )
        for upd in updates:
            offset = upd.update_id + 1
            msg = upd.edited_channel_post
            if msg and msg.chat.id == channel_id and check(msg):
                return msg
    raise AssertionError("edited message was not received in aggregator channel")
