from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from plugins.bot.constants import CANCEL, MAX_LENGTH_CATEGORY_DESC
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.senders import send_message_to_admins
from plugins.bot.utils.validator import MessageValidator


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/:edit/desc/$") & custom_filters.admin_only,
)
async def edit_category_desc(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        "ОК. Ты меняешь описание канала категории.\n\n"
        f"**Введи новое описание** или {CANCEL}"
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_category_desc_waiting_input,
        client,
        callback_query,
    )


async def edit_category_desc_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data, back_step=2)

    validator = MessageValidator(
        menu=menu,
        message=message,
        delete_message=callback_query.message,
    )
    if not await validator.is_text():
        return
    if not await validator.text_length_less_than(MAX_LENGTH_CATEGORY_DESC):
        return

    category_id = menu.path.get_value("c")

    new_desc = message.text
    await client.set_chat_description(chat_id=category_id, description=new_desc)

    cat_link = await get_channel_formatted_link(category_id)
    success_text = f"✅ Описание категории **{cat_link}** изменено на **{new_desc}**"
    await message.reply_text(
        text=success_text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    # Удаляем предыдущее меню
    await callback_query.message.delete()

    await send_message_to_admins(client, callback_query, success_text)
