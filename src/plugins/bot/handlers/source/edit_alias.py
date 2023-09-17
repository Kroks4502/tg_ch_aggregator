from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from models import Source
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.senders import send_message_to_admins
from utils.menu.path import Path

REWRITE_TEXT_TPL = "✅ Установлен режим {} сообщений для источника {}"


@Client.on_callback_query(
    filters.regex(r"/s/-\d+/:edit/alias/$") & custom_filters.admin_only,
)
async def edit_alias(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)
    source_id = path.get_value("s")
    source_obj = Source.get(source_id)

    input_wait_manager.add(
        chat_id=callback_query.message.chat.id,
        func=edit_alias_waiting_input,
        client=client,
        callback_query=callback_query,
        source_obj=source_obj,
    )

    await callback_query.message.reply(
        f"ОК. Ты меняешь название для источника `{source_obj.title}`.\n\n"
        f"**Введи новое** или {CANCEL}"
    )


async def edit_alias_waiting_input(  # noqa: C901
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
    source_obj: Source,
):
    menu = Menu(callback_query.data)

    new_message = await message.reply_text("⏳ Проверка…")

    async def edit_text(text):
        await new_message.edit_text(
            text,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    new_title_alias = message.text
    if len(new_title_alias) > 100:
        await edit_text("❌ Название источника не может превышать 100 символов.")
        return

    src_link = await get_channel_formatted_link(source_obj.id)

    if new_title_alias == source_obj.title:
        source_obj.title_alias = None
        success_text = f"✅ Источник **{src_link}** получил оригинальное название"
    else:
        source_obj.title_alias = new_title_alias
        success_text = (
            f"✅ Источник **{src_link}** получил название **{source_obj.title_alias}**"
        )

    source_obj.save()
    await edit_text(success_text)

    await send_message_to_admins(client, callback_query, success_text)