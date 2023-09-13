from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import User
from plugins.bot.constants import CONF_DEL_BTN_TEXT, CONF_DEL_TEXT_TPL
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_user_formatted_link
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/a/\d+/:delete/$') & custom_filters.admin_only,
)
async def confirmation_delete_admin(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    admin_id = menu.path.get_value('a')
    admin_obj: User = User.get(admin_id)

    menu.add_row_button(CONF_DEL_BTN_TEXT, ':y')

    text = await menu.get_text(
        admin_obj=admin_obj,
        last_text=CONF_DEL_TEXT_TPL.format('администратора'),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/a/\d+/:delete/:y/$') & custom_filters.admin_only,
)
async def delete_admin(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    admin_id = menu.path.get_value('a')
    admin_obj: User = User.get(admin_id)

    admin_obj.delete_instance()
    User.clear_actual_cache()

    adm_link = await get_user_formatted_link(admin_obj.id)
    text = f'✅ Администратор **{adm_link}** удален'
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
