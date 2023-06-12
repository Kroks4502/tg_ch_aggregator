import peewee
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Category, Filter, Source
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.inline_keyboard import ButtonData, Menu


@Client.on_callback_query(
    filters.regex(r'/s/$'),
)
async def list_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(path=callback_query.data, back_step=2)

    category_id = menu.path.get_value('c')
    category_obj = Category.get(category_id) if category_id else None
    if category_obj and is_admin(callback_query.from_user.id):
        menu.add_row_many_buttons(
            ('➕', ':add'),  # Добавить источник в категорию
            ('📝', '../:edit'),  # Редактировать категорию (изменить канал)
            ('✖️', '../:delete'),  # Удалить категорию
        )

    query = (
        Source.select(
            Source.id,
            Source.title,
            Source.cleanup_regex,
            peewee.fn.Count(Filter.id).alias('count'),
        )
        .where(Source.category == category_obj.id if category_obj else True)
        .join(Filter, peewee.JOIN.LEFT_OUTER)
        .group_by(Source.id)
    )  # Запрашиваем список источников
    menu.add_rows_from_data(
        data=[ButtonData(i.title, i.id, i.count + len(i.cleanup_regex)) for i in query]
    )

    text = await menu.get_text(
        category_obj=category_obj,
        last_text='' if category_obj else '**Источники**',
    )
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
