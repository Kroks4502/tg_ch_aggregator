import logging
import re

import peewee
from aiogram.types import Message
from telethon import utils as tl_utils
from telethon.errors import UserAlreadyParticipantError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest

from clients import telethon_user_client
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

    entity, source_link = await _get_channel_entity(message)
    validators.is_channel(entity)

    entity = await _join_to_chat(entity, source_link)

    category_id = menu.path.get_value("c")
    source_obj = _create_source(entity, category_id)

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


async def _get_channel_entity(message: Message):
    """
    Получить Telethon-сущность канала по ссылке из сообщения.
    Возвращает (entity, source_link).
    """
    try:
        source_link = message.text.strip(" /\n")
        if re.match(r"https://t\.me/(\+|joinchat/)", source_link):
            # Invite link — сначала получим информацию (не вступаем)
            from telethon.tl.functions.messages import CheckChatInviteRequest

            hash_val = re.sub(r"https://t\.me/(\+|joinchat/)", "", source_link)
            invite_info = await telethon_user_client(CheckChatInviteRequest(hash=hash_val))
            return invite_info, source_link

        # @username или t.me/channel
        username = re.sub(r"(https://)|((\.|)t\.me(/|))", "", source_link)
        entity = await telethon_user_client.get_entity(username)
        return entity, username

    except Exception as e:
        logging.error(e, exc_info=True)
        raise ValueError(f"{ERROR_UNKNOWN}\n\n{e}")


async def _join_to_chat(entity, source_link: str):
    """Вступить в канал и вернуть обновлённую сущность."""
    try:
        if re.match(r"https://t\.me/(\+|joinchat/)", source_link):
            hash_val = re.sub(r"https://t\.me/(\+|joinchat/)", "", source_link)
            result = await telethon_user_client(ImportChatInviteRequest(hash=hash_val))
            return result.chats[0]

        await telethon_user_client(JoinChannelRequest(entity))
        return entity

    except UserAlreadyParticipantError:
        return entity
    except Exception as e:
        logging.error(e, exc_info=True)
        raise ValueError(f"{ERROR_JOIN_CHAT_FAILED}\n\n{e}")


def _create_source(entity, category_id: int) -> Source:
    # Telethon возвращает bare channel_id; конвертируем в marked формат (-100xxx)
    channel_id = tl_utils.get_peer_id(entity)
    title = getattr(entity, "title", str(channel_id))
    try:
        source_obj = Source.get_or_none(id=channel_id)

        if not source_obj:
            return Source.create(
                id=channel_id,
                title=title,
                category=category_id,
            )

        source_obj.category = category_id
        source_obj.title = title
        source_obj.is_deleted = False
        source_obj.save()

        return source_obj
    except peewee.IntegrityError:
        raise ValueError(ERROR_EXISTED_SOURCE)
