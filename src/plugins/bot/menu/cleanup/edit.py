from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from models import GlobalSettings, Source
from plugins.bot.constants import INVALID_PATTERN_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins

ASK_TEXT_TPL = 'ОК. Ты изменяешь {} очистки текста `{}`{}.\n\n**Введи новый паттерн:**'
SUC_TEXT_TPL = '✅ {} очистки текста изменен с `{}` на `{}` {}'


@Client.on_callback_query(
    filters.regex(r'/cl/\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_cleanup_regex(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)

    cleanup_id = path.get_value('cl')
    source_id = path.get_value('s')
    source_obj: Source = Source.get(source_id) if source_id else None

    if source_obj:
        pattern = source_obj.cleanup_list[cleanup_id]
        src_link = await get_channel_formatted_link(source_obj.id)
        text = ASK_TEXT_TPL.format('паттерн', pattern, f' для источника {src_link}')
    else:
        global_settings_obj = GlobalSettings.get(key='cleanup_list')
        pattern = global_settings_obj.value[cleanup_id]
        text = ASK_TEXT_TPL.format('общий паттерн', pattern, '')

    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_cleanup_regex_wait_input,
        client,
        callback_query,
        source_obj,
        cleanup_id,
    )


async def edit_cleanup_regex_wait_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
    source_obj: Source,
    cleanup_id: int,
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

    pattern_new = str(message.text)
    if not is_valid_pattern(pattern_new):
        await reply(INVALID_PATTERN_TEXT)
        return

    if source_obj:
        cleanup_list = source_obj.cleanup_list
        pattern_old = cleanup_list[cleanup_id]
        cleanup_list[cleanup_id] = pattern_new
        source_obj.save()
        src_link = await get_channel_formatted_link(source_obj.id)

        text = SUC_TEXT_TPL.format(
            'Паттерн',
            pattern_old,
            pattern_new,
            f'для источника **{src_link}**',
        )
    else:
        global_settings_obj = GlobalSettings.get(key='cleanup_list')
        cleanup_list = global_settings_obj.value
        pattern_old = cleanup_list[cleanup_id]
        cleanup_list[cleanup_id] = pattern_new
        global_settings_obj.save()
        GlobalSettings.clear_actual_cache()

        text = SUC_TEXT_TPL.format(
            'Общий паттерн',
            pattern_old,
            pattern_new,
            '',
        )

    await reply(text)

    await send_message_to_admins(client, callback_query, text)
