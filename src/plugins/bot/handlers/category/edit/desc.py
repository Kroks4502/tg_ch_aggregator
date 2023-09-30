from pyrogram import Client
from pyrogram.types import Message

from plugins.bot import router, validators
from plugins.bot.constants.settings import MAX_LENGTH_CATEGORY_DESC
from plugins.bot.handlers.category.common.constants import (
    ACTION_ENTER_CATEGORY_DESC,
    EDIT_CATEGORY_DESC_TEXT,
    SUCCESS_CATEGORY_EDIT_DESC_TEXT,
)
from plugins.bot.handlers.category.common.utils import (
    get_category_menu_success_text,
    get_edit_dialog_text,
)
from plugins.bot.menu import Menu


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_desc_waiting_input(
    client: Client,
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_DESC)

    category_id = menu.path.get_value("c")

    chat = await client.get_chat(chat_id=category_id)

    old_desc = chat.description
    new_desc = message.text
    await chat.set_description(description=new_desc)

    return await get_category_menu_success_text(
        category_id=category_id,
        action=SUCCESS_CATEGORY_EDIT_DESC_TEXT.format(new_desc, old_desc),
    )


@router.page(
    path=r"/c/-\d+/:edit/desc/",
    reply=True,
    add_wait_for_input=edit_category_desc_waiting_input,
)
async def edit_category_desc(menu: Menu):
    category_id = menu.path.get_value("c")
    return await get_edit_dialog_text(
        category_id=category_id,
        doing=EDIT_CATEGORY_DESC_TEXT,
        action=ACTION_ENTER_CATEGORY_DESC,
    )
