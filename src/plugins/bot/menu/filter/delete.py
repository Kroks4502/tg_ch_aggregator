from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.utils import custom_filters
from plugins.bot.utils.inline_keyboard import Menu
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/f/\d+/:delete/$') & custom_filters.admin_only,
)
async def confirmation_delete_filter(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    filter_id = menu.path.get_value('f')
    filter_obj: Filter = Filter.get(filter_id)

    menu.add_row_button('❌ Подтвердить удаление', ':y')

    text = await menu.get_text(filter_obj=filter_obj)
    text += '\n\nТы **удаляешь** фильтр!'
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
    Filter.clear_actual_cache()

    filter_type_text = FILTER_TYPES_BY_ID.get(filter_obj.type)
    mid_text = f'типа **{filter_type_text}** c паттерном `{filter_obj.pattern}` удален'
    if filter_obj.source:
        src_link = await get_channel_formatted_link(filter_obj.source.tg_id)
        text = f'✅ Фильтр {mid_text} из источника **{src_link}**'
    else:
        text = f'✅ Общий фильтр {mid_text}'

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
