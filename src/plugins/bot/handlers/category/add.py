from aiogram import Bot
from aiogram.types import Message
from telethon import utils as tl_utils
from telethon.tl.functions.channels import CreateChannelRequest, EditAdminRequest
from telethon.tl.types import ChatAdminRights

from clients import telethon_user_client
from models import Category
from plugins.bot import router, validators
from plugins.bot.constants.settings import MAX_LENGTH_CATEGORY_NAME
from plugins.bot.constants.text import CATEGORY_NAME_TPL, DIALOG
from plugins.bot.handlers.category.common.constants import (
    ACTION_ENTER_CATEGORY_NAME,
    ADD_CATEGORY_TEXT,
)
from plugins.bot.handlers.category.common.utils import get_category_menu_success_text


@router.wait_input(initial_text="⏳ Создаю канал для категории…", send_to_admins=True)
async def add_category_waiting_input(
    bot: Bot,
    message: Message,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_NAME)

    bot_me = await bot.me()

    # Создать канал через userbot (Telethon)
    result = await telethon_user_client(
        CreateChannelRequest(
            title=CATEGORY_NAME_TPL.format(message.text),
            about=f"Создан ботом {bot_me.username}",
            megagroup=False,
        )
    )
    new_channel = result.chats[0]
    # Telethon возвращает bare channel_id; конвертируем в marked формат (-100xxx)
    category_id = tl_utils.get_peer_id(new_channel)

    # Назначить бота администратором созданного канала
    bot_entity = await telethon_user_client.get_entity(bot_me.id)
    await telethon_user_client(
        EditAdminRequest(
            channel=new_channel,
            user_id=bot_entity,
            admin_rights=ChatAdminRights(
                change_info=True,
                post_messages=True,
                edit_messages=True,
                delete_messages=True,
                ban_users=False,
                invite_users=True,
                pin_messages=False,
                add_admins=True,
                anonymous=False,
                manage_call=True,
                other=True,
            ),
            rank="",
        )
    )

    category_obj = Category.create(
        id=category_id,
        title=new_channel.title,
    )
    return await get_category_menu_success_text(
        category_id=category_obj.id,
        action="создана",
    )


@router.page(
    path=r"/c/:add/",
    reply=True,
    add_wait_for_input=add_category_waiting_input,
)
async def add_category():
    return DIALOG.format(
        doing=ADD_CATEGORY_TEXT,
        action=ACTION_ENTER_CATEGORY_NAME,
    )
