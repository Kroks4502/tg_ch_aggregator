from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import GlobalSettings, Source
from plugins.bot.constants import CONF_DEL_TEXT_TPL
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.senders import send_message_to_admins

SUC_TEXT_TPL = "✅ {} очистки текста `{}` удален {}"


@Client.on_callback_query(
    filters.regex(r"/cl/\d+/:delete/$") & custom_filters.admin_only,
)
async def confirmation_delete_cleanup_regex(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None
    if source_obj:
        pattern = source_obj.cleanup_list[cleanup_id]
    else:
        cleanup_list = GlobalSettings.get(key="cleanup_list").value
        pattern = cleanup_list[cleanup_id]

    menu.add_button.confirmation_delete()

    text = await menu.get_text(
        source_obj=source_obj,
        cleanup_pattern=pattern,
        last_text=CONF_DEL_TEXT_TPL.format("паттерн очистки текста"),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r"/cl/\d+/:delete/:y/$") & custom_filters.admin_only,
)
async def delete_cleanup_regex(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    cleanup_id = menu.path.get_value("cl")

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        pattern = source_obj.cleanup_list.pop(cleanup_id)
        source_obj.save()
        src_link = await get_channel_formatted_link(source_obj.id)
        text = SUC_TEXT_TPL.format("Паттерн", pattern, f"из источника **{src_link}**")
    else:
        global_settings_obj = GlobalSettings.get(key="cleanup_list")
        pattern = global_settings_obj.value.pop(cleanup_id)
        global_settings_obj.save()
        text = SUC_TEXT_TPL.format("Общий паттерн", pattern, "")

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
