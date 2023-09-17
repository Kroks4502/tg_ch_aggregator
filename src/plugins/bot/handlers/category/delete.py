from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/:delete/$") & custom_filters.admin_only,
)
async def confirmation_delete_category(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    menu.add_button.confirmation_delete()

    text = await menu.get_text(
        category_obj=category_obj,
        last_text=CONF_DEL_TEXT_TPL.format("категорию"),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/:delete/:y/$") & custom_filters.admin_only,
)
async def delete_category(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    category_id = menu.path.get_value("c")
    category_obj: Category = Category.get(category_id)

    category_obj.delete_instance()

    cat_link = await get_channel_formatted_link(category_obj.id)
    text = f"✅ Категория **{cat_link}** удалена"
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
