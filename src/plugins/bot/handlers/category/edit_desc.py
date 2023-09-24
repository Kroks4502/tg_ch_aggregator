from pyrogram import Client
from pyrogram.types import Message

from plugins.bot import router, validators
from plugins.bot.constants import CANCEL, MAX_LENGTH_CATEGORY_DESC
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_desc_waiting_input(
    client: Client,
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_DESC)

    category_id = menu.path.get_value("c")

    new_desc = message.text
    await client.set_chat_description(chat_id=category_id, description=new_desc)

    cat_link = await get_channel_formatted_link(category_id)
    return f"✅ Описание категории **{cat_link}** изменено на **{new_desc}**"


@router.page(
    path=r"/c/-\d+/:edit/desc/",
    reply=True,
    add_wait_for_input=edit_category_desc_waiting_input,
)
async def edit_category_desc():
    return (
        "ОК. Ты меняешь описание канала категории.\n\n"
        f"**Введи новое описание** или {CANCEL}"
    )
