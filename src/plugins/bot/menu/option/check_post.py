from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from common import get_message_link
from models import MessageHistory
from plugins.bot.utils import custom_filters
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu


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

    history_obj: MessageHistory = MessageHistory.get_or_none(
        source_id=chat_id, source_message_id=message_id
    )

    if not history_obj:
        history_obj = MessageHistory.get_or_none(
            source_forward_from_chat_id=chat_id,
            source_forward_from_message_id=message_id,
        )

    if history_obj.filter_id:
        menu.add_row_button('Перейти к фильтру', f'f/{history_obj.filter_id}')
        msg_link = get_message_link(
            history_obj.source_id, history_obj.source_message_id
        )
        await reply(f'⚠ [Пост]({msg_link}) был отфильтрован')
        return

    msg_link = get_message_link(
        message.forward_from_chat.id, message.forward_from_message_id
    )
    if not history_obj:
        await reply(f'❌ [Поста]({msg_link}) нет в истории')
        return

    await reply(
        f'✅ [Пост]({msg_link}) '
        f'из источника `{history_obj.source.title}` '
        f'был опубликован в категории [{history_obj.category.title}]'
        f'({get_message_link(history_obj.category_id, history_obj.category_message_id)})'
    )
