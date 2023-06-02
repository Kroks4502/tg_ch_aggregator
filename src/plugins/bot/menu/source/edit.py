from peewee import JOIN, fn
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Source
from plugins.bot.utils import custom_filters
from plugins.bot.utils.inline_keyboard import ButtonData, Menu
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.senders import send_message_to_admins


@Client.on_callback_query(
    filters.regex(r'/s/\d+/:edit/$') & custom_filters.admin_only,
)
async def edit_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id)
    text = await menu.get_text(source_obj=source_obj)
    text += '\n\nТы **меняешь категорию** у источника.\n' 'Выбери новую категорию:'

    query = (
        Category.select(
            Category.id,
            Category.title,
            fn.Count(Source.id).alias('amount'),
        )
        .join(Source, JOIN.LEFT_OUTER)
        .group_by(Category.id)
    )
    menu.add_rows_from_data(
        data=[ButtonData(i.title, i.id, i.amount) for i in query],
    )

    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )


@Client.on_callback_query(
    filters.regex(r'/s/\d+/:edit/\d+/$') & custom_filters.admin_only,
)
async def new_source_category(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data, back_step=2)

    source_id = menu.path.get_value('s')
    source_obj = Source.get(source_id)

    old_category_obj = source_obj.category

    new_category_id = menu.path.get_value(':edit')
    new_category_obj = Category.get(new_category_id)

    source_obj.category = new_category_obj
    source_obj.save()
    Source.clear_actual_cache()

    src_link = await get_channel_formatted_link(source_obj.tg_id)
    cat_link_old = await get_channel_formatted_link(old_category_obj.tg_id)
    cat_link_new = await get_channel_formatted_link(new_category_obj.tg_id)
    text = f'✅ Категория источника **{src_link}** изменена с **{cat_link_old}** на **{cat_link_new}**'
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )

    await send_message_to_admins(client, callback_query, text)
