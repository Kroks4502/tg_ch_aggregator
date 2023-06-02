from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from clients import user
from models import Admin
from plugins.bot.utils import custom_filters
from plugins.bot.utils.inline_keyboard import Menu
from plugins.bot.utils.links import get_user_formatted_link


@Client.on_callback_query(
    filters.regex(r'/a/\d+/$') & custom_filters.admin_only,
)
async def detail_admin(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    admin_id = menu.path.get_value('a')
    admin_obj: Admin = Admin.get(admin_id)

    adm_link = await get_user_formatted_link(admin_obj.tg_id)
    text = f'**{adm_link}**'
    if admin_obj.tg_id != user.me.id:
        menu.add_row_button('✖️ Удалить', ':delete')
    else:
        text = f'Основной пользователь\n{text}'

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )