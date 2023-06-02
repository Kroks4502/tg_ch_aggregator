from pyrogram import Client, filters
from pyrogram.types import (
    CallbackQuery,
    Message,
)

from common import get_message_link
from models import Source, CategoryMessageHistory, FilterMessageHistory

from plugins.bot.utils import custom_filters
from plugins.bot.utils.inline_keyboard import Menu
from plugins.bot.utils.managers import input_wait_manager


@Client.on_callback_query(
    filters.regex(r'/:check_post/$') & custom_filters.admin_only,
)
async def check_post(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты хочешь проверить есть ли пост в истории.\n\n'
        '**Перешли пост в этот чат и я проверю.**'
    )
    input_wait_manager.add(
        callback_query.message.chat.id,
        check_post_waiting_forwarding,
        client,
    )


async def check_post_waiting_forwarding(_, message: Message):
    menu = Menu('/./')

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )

    if not message.forward_from_chat:
        await reply('🫥 Это не пересланный пост')
        return

    chat_id = message.forward_from_chat.id
    message_id = message.forward_from_message_id
    source = Source.get_or_none(tg_id=chat_id)
    m_history_obj = None
    f_history_obj = None
    if source:
        m_history_obj = CategoryMessageHistory.get_or_none(
            source=source, source_message_id=message_id, deleted=False
        )
        f_history_obj = FilterMessageHistory.get_or_none(
            source=source,
            source_message_id=message_id,
        )

    if not m_history_obj:
        m_history_obj = CategoryMessageHistory.get_or_none(
            forward_from_chat_id=chat_id,
            forward_from_message_id=message_id,
            deleted=False,
        )

    if f_history_obj:
        menu.add_row_button('Перейти к фильтру', f'f/{f_history_obj.filter.id}')
        msg_link = get_message_link(
            f_history_obj.source.tg_id, f_history_obj.source_message_id
        )
        await reply(f'⚠️ [Пост]({msg_link}) был отфильтрован')
        return

    msg_link = get_message_link(
        message.forward_from_chat.id, message.forward_from_message_id
    )
    if not m_history_obj:
        await reply(f'❌ [Поста]({msg_link}) нет в истории')
        return

    await reply(
        f'✅ [Пост]({msg_link}) '
        f'из источника `{m_history_obj.source.title}` '
        f'был опубликован в категории [{m_history_obj.category.title}]'
        f'({get_message_link(m_history_obj.category.tg_id, m_history_obj.message_id)})'
    )
