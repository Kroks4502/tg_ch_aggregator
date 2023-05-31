import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message, InlineKeyboardMarkup

from filter_types import FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.menu.filter.detail import detail_filter
from plugins.bot.utils import custom_filters, buttons
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.path import Path
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/f_\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_body_filter(client: Client, callback_query: CallbackQuery):
    path = Path(callback_query.data)
    chat_id = callback_query.message.chat.id
    filter_id = int(path.get_value('f'))
    filter_obj: Filter = Filter.get_or_none(id=filter_id)

    text = 'ОК. Ты изменяешь '
    text += (
        'фильтр для источника '
        f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        if filter_obj.source
        else 'общий фильтр '
    )
    text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** с паттерном '
        f'`{filter_obj.pattern}`.\n\n'
        '**Введи новый паттерн фильтра:**'
    )

    await callback_query.answer()
    await callback_query.message.reply(text, disable_web_page_preview=True)
    input_wait_manager.add(
        chat_id, edit_body_filter_wait_input, client, callback_query, filter_obj
    )


async def edit_body_filter_wait_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
    filter_obj: Filter,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_footer(
                    path,
                    back_title='Параметры',
                )
            ),
            disable_web_page_preview=True,
        )

    filter_obj.pattern = message.text
    filter_obj.save()
    Filter.clear_actual_cache()

    if filter_obj.source:
        success_text = (
            '✅ Фильтр для источника '
            f'{await get_channel_formatted_link(filter_obj.source.tg_id)} '
        )
    else:
        success_text = '✅ Общий фильтр '
    success_text += (
        f'типа **{FILTER_TYPES_BY_ID.get(filter_obj.type)}** '
        f'с паттерном `{filter_obj.pattern}` изменен'
    )

    await reply(success_text)

    callback_query.data = path.get_prev()
    await detail_filter(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)
