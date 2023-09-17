from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from filter_types import FilterType
from models import Filter
from plugins.bot.menu import Menu
from plugins.bot.utils.checks import is_admin


@Client.on_callback_query(filters.regex(r"/f/\d+/$"))
async def detail_filter(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    filter_id = menu.path.get_value("f")
    filter_obj: Filter = Filter.get(filter_id)

    if is_admin(callback_query.from_user.id):
        if filter_obj.type not in (
            FilterType.ENTITY_TYPE.value,
            FilterType.MESSAGE_TYPE.value,
        ):
            menu.add_button.edit()
        menu.add_button.delete()

    text = await menu.get_text(filter_obj=filter_obj)
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
