from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Source
from plugins.bot.constants import CONF_DEL_BTN_TEXT, CONF_DEL_TEXT_TPL
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r"/s/-\d+/:delete/$") & custom_filters.admin_only,
)
async def confirmation_delete_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    menu.add_row_button(CONF_DEL_BTN_TEXT, ":y")

    text = await menu.get_text(
        source_obj=source_obj,
        last_text=CONF_DEL_TEXT_TPL.format("источник"),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/s/-\d+/:delete/:y/$") & custom_filters.admin_only,
)
async def delete_source(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    source_obj.delete_instance()

    src_link = await get_channel_formatted_link(source_obj.id)
    text = f"✅ Источник **{src_link}** удален"
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
