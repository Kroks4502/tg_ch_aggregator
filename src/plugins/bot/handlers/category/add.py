from pyrogram import Client
from pyrogram.types import ChatPrivileges, Message

from clients import user_client
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
    client: Client,
    message: Message,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_NAME)

    new_channel = await user_client.create_channel(
        CATEGORY_NAME_TPL.format(message.text),
        f"Создан ботом {client.me.username}",
    )

    await new_channel.promote_member(
        client.me.id,
        ChatPrivileges(
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_promote_members=True,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_invite_users=True,
        ),
    )

    category_obj = Category.create(
        id=new_channel.id,
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
