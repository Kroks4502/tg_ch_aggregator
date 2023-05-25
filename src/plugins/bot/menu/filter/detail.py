import logging

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from filter_types import FilterType, FILTER_TYPES_BY_ID
from models import Filter
from plugins.bot.utils import buttons
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.path import Path


@Client.on_callback_query(
    filters.regex(r'/f_\d+/$'),
)
async def detail_filter(
    _,
    callback_query: CallbackQuery,
    *,
    needs_an_answer: bool = True,
):
    logging.debug(callback_query.data)

    path = Path(callback_query.data)
    filter_obj: Filter = Filter.get(id=int(path.get_value('f')))

    inline_keyboard = []
    if is_admin(callback_query.from_user.id):
        if filter_obj.type in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            inline_keyboard.append(
                [
                    InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
                ],
            )
        else:
            inline_keyboard.append(
                [
                    InlineKeyboardButton(f'📝', callback_data=path.add_action('edit')),
                    InlineKeyboardButton('✖️', callback_data=path.add_action('delete')),
                ],
            )
    inline_keyboard += buttons.get_footer(path)

    if filter_obj.source:
        text = (
            f'Источник: **{await get_channel_formatted_link(filter_obj.source.tg_id)}**'
        )
    else:
        text = '**Общий фильтр**'
    text += (
        f'\nТип фильтра: **{FILTER_TYPES_BY_ID.get(filter_obj.type)}**'
        f'\nПаттерн: `{filter_obj.pattern}`'
    )
    if needs_an_answer:
        await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True,
    )
