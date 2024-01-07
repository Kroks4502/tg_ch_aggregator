import logging
import re

import peewee
from pyrogram.errors import RPCError, UserAlreadyParticipant
from pyrogram.types import Chat, ChatPreview, Message

from clients import user_client
from models import Source
from plugins.bot import router, validators
from plugins.bot.constants.text import ERROR_UNKNOWN
from plugins.bot.handlers.source.common.constants import (
    ACTION_ENTER_SOURCE_LINK,
    ERROR_EXISTED_SOURCE,
    ERROR_JOIN_CHAT_FAILED,
)
from plugins.bot.handlers.source.common.utils import (
    get_dialog_text,
    get_source_menu_success_text,
)
from plugins.bot.menu import Menu
from plugins.bot.utils.chat_info import get_chat_info
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(initial_text="⏳ Проверка…", send_to_admins=True)
async def add_source_waiting_input(
    message: Message,
    menu: Menu,
):
    validators.is_text(message)

    chat, chat_id = await _get_chat(message)
    validators.is_channel(chat)

    chat = await _join_to_chat(chat_id)

    category_id = menu.path.get_value("c")
    source_obj = _create_source(chat, category_id)

    cat_link = await get_channel_formatted_link(category_id)
    chat_info = await get_chat_info(source_obj)
    return await get_source_menu_success_text(
        source_id=source_obj.id,
        action=f"добавлен в категорию **{cat_link}**\n\n{chat_info}",
    )


@router.page(
    path=r"/c/-\d+/s/:add/",
    reply=True,
    add_wait_for_input=add_source_waiting_input,
)
async def add_source(menu: Menu):
    return await get_dialog_text(
        category_id=menu.path.get_value("c"),
        doing="добавляешь",
        action=ACTION_ENTER_SOURCE_LINK,
    )


async def _get_chat(message: Message) -> tuple[Chat | ChatPreview, int | str]:
    try:
        source_link = message.text.strip(" /\n")
        if source_link.startswith("https://t.me/+"):
            return await user_client.get_chat(source_link), source_link

        chat_username = re.sub(
            pattern=r"(https://)|((\.|)t\.me(/|))",
            repl="",
            string=source_link,
        )
        return await user_client.get_chat(chat_username), chat_username

    except RPCError as e:
        logging.error(e, exc_info=True)
        raise ValueError(f"{ERROR_UNKNOWN}\n\n{e}")


async def _join_to_chat(source_link: str) -> Chat:
    try:
        return await user_client.join_chat(source_link)
    except UserAlreadyParticipant:
        return await user_client.get_chat(source_link)
    except RPCError as e:
        logging.error(e, exc_info=True)
        raise ValueError(f"{ERROR_JOIN_CHAT_FAILED}\n\n{e}")


def _create_source(chat: Chat, category_id: int) -> Source:
    try:
        return Source.create(id=chat.id, title=chat.title, category=category_id)
    except peewee.IntegrityError:
        raise ValueError(ERROR_EXISTED_SOURCE)
