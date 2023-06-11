from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from models import GlobalSettings, Source
from plugins.bot.constants import INVALID_PATTERN_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.inline_keyboard import Menu
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins

ASK_TEXT_TPL = 'ОК. Ты добавляешь {} очистки текста{}.\n\n**Введи паттерн:**'
SUC_TEXT_TPL = '✅ {} очистки текста `{}` добавлен {}'


@Client.on_callback_query(
    filters.regex(r'/cl/:add/$') & custom_filters.admin_only,
)
async def add_cleanup_regex(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)
    source_id = path.get_value('s')
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        src_link = await get_channel_formatted_link(source_obj.tg_id)
        text = ASK_TEXT_TPL.format('паттерн', f' для источника {src_link}')
    else:
        text = ASK_TEXT_TPL.format('общий паттерн', '')

    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        callback_query.message.chat.id,
        add_cleanup_regex_waiting_input,
        client,
        callback_query,
        source_obj,
    )


async def add_cleanup_regex_waiting_input(
    client: Client,
    message: Message,
    callback_query,
    source_obj: Optional[Source],
):
    menu = Menu(callback_query.data)

    async def reply(t):
        await message.reply_text(
            text=t,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    pattern = message.text
    if not is_valid_pattern(pattern):
        await reply(INVALID_PATTERN_TEXT)
        return

    if source_obj:
        source_obj.cleanup_regex.append(pattern)
        source_obj.save()

        src_link = await get_channel_formatted_link(source_obj.tg_id)
        text = SUC_TEXT_TPL.format('Паттерн', pattern, f'для источника {src_link}')
    else:
        global_settings_obj = GlobalSettings.get(key='cleanup_regex')
        global_settings_obj.value.append(pattern)
        global_settings_obj.save()
        GlobalSettings.clear_actual_cache()

        text = SUC_TEXT_TPL.format('Общий паттерн', pattern, '')

    await reply(text)

    await send_message_to_admins(client, callback_query, text)
