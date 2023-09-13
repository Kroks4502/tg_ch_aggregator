from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.constants import CONF_DEL_BTN_TEXT, CONF_DEL_TEXT_TPL
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.menu import Menu
from plugins.bot.utils.senders import send_message_to_admins

SUC_TEXT_TPL = '✅ {} типа **{}** c паттерном `{}` удален'


@Client.on_callback_query(
    filters.regex(r'/f/\d+/:delete/$') & custom_filters.admin_only,
)
async def confirmation_delete_filter(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    filter_id = menu.path.get_value('f')
    filter_obj: Filter = Filter.get(filter_id)

    menu.add_row_button(CONF_DEL_BTN_TEXT, ':y')

    text = await menu.get_text(
        filter_obj=filter_obj,
        last_text=CONF_DEL_TEXT_TPL.format('фильтр'),
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/f/\d+/:delete/:y/$') & custom_filters.admin_only,
)
async def delete_filter(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=3)

    filter_id = menu.path.get_value('f')
    filter_obj: Filter = Filter.get(filter_id)

    filter_obj.delete_instance()

    if filter_obj.source:
        src_link = await get_channel_formatted_link(filter_obj.source.id)
        title = f'Фильтр источника **{src_link}**'
    else:
        title = 'Общий фильтр'
    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    text = SUC_TEXT_TPL.format(title, filter_type_text, filter_obj.pattern)

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
