from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from clients import user
from models import Source
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.senders import send_message_to_admins

REWRITE_TEXT_TPL = '✅ Установлен режим {} сообщений для источника {}'


@Client.on_callback_query(
    filters.regex(r'/s/\d+/:(on|off)_rewrite/$') & custom_filters.admin_only,
)
async def set_rewrite(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data)

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id)

    src_link = await get_channel_formatted_link(source_obj.tg_id)
    if callback_query.data.endswith('off_rewrite/'):
        source_obj.is_rewrite = False
        text = REWRITE_TEXT_TPL.format('пересылки', src_link)
        chat = await user.get_chat(source_obj.tg_id)
        if chat.has_protected_content:
            text += ', но канал запрещает пересылку сообщений! ⚠'
    else:
        source_obj.is_rewrite = True
        text = REWRITE_TEXT_TPL.format('перепечатывания', src_link)

    source_obj.save()

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
