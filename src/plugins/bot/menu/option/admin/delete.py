import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from models import Admin
from plugins.bot.menu.option.admin.list import list_admins
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_user_formatted_link
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'u_\d+/:delete/') & custom_filters.admin_only,
)
async def delete_admin(client: Client, callback_query: CallbackQuery):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    admin_id = int(path.get_value('u'))
    admin_obj: Admin = Admin.get(id=admin_id)
    text = f'**{await get_user_formatted_link(admin_obj.tg_id)}**'
    if path.with_confirmation:
        q = Admin.delete().where(Admin.id == admin_id)
        q.execute()

        Admin.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Администратор удален')
        await list_admins(client, callback_query, needs_an_answer=False)

        await send_message_to_admins(
            client, callback_query, f'❌ Удален администратор {text}'
        )
        return

    text += '\n\nТы **удаляешь** администратора!'

    inline_keyboard = [
        [
            InlineKeyboardButton('❌ Подтвердить удаление', callback_data=f'{path}/'),
        ]
    ]
    inline_keyboard += buttons.get_footer(path)

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )
