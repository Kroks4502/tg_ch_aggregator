from pyrogram import Client
from pyrogram.types import Message

from models import Category
from plugins.bot import router, validators
from plugins.bot.constants.settings import MAX_LENGTH_CATEGORY_NAME
from plugins.bot.constants.text import CATEGORY_NAME_TPL
from plugins.bot.handlers.category.common.constants import (
    ACTION_ENTER_CATEGORY_NAME,
    EDIT_CATEGORY_TITLE_TEXT,
    SUCCESS_CATEGORY_EDIT_TITLE_TEXT,
)
from plugins.bot.handlers.category.common.utils import (
    get_category_menu_success_text,
    get_edit_dialog_text,
)
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_title_waiting_input(
    client: Client,
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_NAME)

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    chat = await client.get_chat(chat_id=category_id)

    old_title = chat.title
    new_title = CATEGORY_NAME_TPL.format(message.text)
    await chat.set_title(title=new_title)

    category_obj.title = new_title
    category_obj.save()

    get_channel_formatted_link.cache_clear()

    return await get_category_menu_success_text(
        category_id=category_id,
        action=SUCCESS_CATEGORY_EDIT_TITLE_TEXT.format(new_title, old_title),
    )


@router.page(
    path=r"/c/-\d+/:edit/title/",
    reply=True,
    add_wait_for_input=edit_category_title_waiting_input,
)
async def edit_category_title(menu: Menu):
    category_id = menu.path.get_value("c")
    return await get_edit_dialog_text(
        category_id=category_id,
        doing=EDIT_CATEGORY_TITLE_TEXT,
        action=ACTION_ENTER_CATEGORY_NAME,
    )
