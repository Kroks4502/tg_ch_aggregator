from aiogram import Bot
from aiogram.types import Message

from plugins.bot import router, validators
from plugins.bot.handlers.category.common.constants import (
    ACTION_SEND_CATEGORY_PHOTO,
    EDIT_CATEGORY_PHOTO_TEXT,
    SUCCESS_CATEGORY_EDIT_PHOTO_TEXT,
)
from plugins.bot.handlers.category.common.utils import (
    get_category_menu_success_text,
    get_edit_dialog_text,
)
from plugins.bot.menu import Menu


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_photo_waiting_input(
    bot: Bot,
    message: Message,
    menu: Menu,
):
    validators.is_photo(message)

    category_id = menu.path.get_value("c")
    # aiogram: message.photo — список PhotoSize от худшего к лучшему качеству
    await bot.set_chat_photo(chat_id=category_id, photo=message.photo[-1].file_id)

    return await get_category_menu_success_text(
        category_id=category_id,
        action=SUCCESS_CATEGORY_EDIT_PHOTO_TEXT,
    )


@router.page(
    path=r"/c/-\d+/:edit/photo/",
    reply=True,
    add_wait_for_input=edit_category_photo_waiting_input,
)
async def edit_category_photo(menu: Menu):
    category_id = menu.path.get_value("c")
    return await get_edit_dialog_text(
        category_id=category_id,
        doing=EDIT_CATEGORY_PHOTO_TEXT,
        action=ACTION_SEND_CATEGORY_PHOTO,
    )
