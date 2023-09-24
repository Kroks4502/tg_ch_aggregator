from pyrogram import Client
from pyrogram.types import Chat, ChatPrivileges, Message

from clients import user
from models import Category
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL, CATEGORY_NAME_TPL, MAX_LENGTH_CATEGORY_NAME
from plugins.bot.utils.links import get_channel_formatted_link


@router.wait_input(initial_text="⏳ Создаю канал для категории…", send_to_admins=True)
async def add_category_waiting_input(
    client: Client,
    message: Message,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_CATEGORY_NAME)

    new_channel: Chat = await user.create_channel(
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

    category_obj: Category = Category.create(
        id=new_channel.id,
        title=new_channel.title,
    )
    cat_link = await get_channel_formatted_link(category_obj.id)

    return f"✅ Категория **{cat_link}** создана"


@router.page(
    path=r"/c/:add/",
    reply=True,
    add_wait_for_input=add_category_waiting_input,
)
async def add_category():
    return (
        "ОК. Ты добавляешь новую категорию, "
        "которая будет получать сообщения из источников. "
        "Будет создан новый канал-агрегатор.\n\n"
        f"**Введи название категории** или {CANCEL}"
    )
