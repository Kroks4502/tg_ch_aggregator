from pyrogram import Client
from pyrogram.types import Message

from models import Category
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL, CATEGORY_NAME_TPL, MAX_LENGTH_CATEGORY_NAME
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(back_step=2, send_to_admins=True)
async def edit_category_name_waiting_input(
    client: Client,
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_NAME)

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    new_title = CATEGORY_NAME_TPL.format(message.text)
    await client.set_chat_title(chat_id=category_id, title=new_title)

    old_title = category_obj.title
    category_obj.title = new_title
    category_obj.save()

    get_channel_formatted_link.cache_clear()

    cat_link = await get_channel_formatted_link(category_id)
    return f"✅ Название категории **{old_title}** изменено на **{cat_link}**"


@router.page(
    path=r"/c/-\d+/:edit/name/",
    reply=True,
    add_wait_for_input=edit_category_name_waiting_input,
)
async def edit_category_name():
    return (
        "ОК. Ты меняешь название канала категории.\n\n"
        f"**Введи новое название** или {CANCEL}"
    )
