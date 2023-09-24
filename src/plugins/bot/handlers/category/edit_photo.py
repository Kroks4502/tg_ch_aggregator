from pyrogram import Client
from pyrogram.types import Message

from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_photo_waiting_input(
    client: Client,
    message: Message,
    menu: Menu,
):
    validators.is_photo(message)

    category_id = menu.path.get_value("c")

    await client.set_chat_photo(chat_id=category_id, photo=message.photo.file_id)

    cat_link = await get_channel_formatted_link(category_id)
    return f"✅ Изображение категории **{cat_link}** изменено"


@router.page(
    path=r"/c/-\d+/:edit/photo/",
    reply=True,
    add_wait_for_input=edit_category_photo_waiting_input,
)
async def edit_category_photo():
    return (
        "ОК. Ты меняешь изображение канала категории.\n\n"
        f"**Отправь новое изображение** или {CANCEL}"
    )
