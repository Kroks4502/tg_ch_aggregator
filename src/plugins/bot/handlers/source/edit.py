from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Source
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters


@Client.on_callback_query(
    filters.regex(r"/s/-\d+/:edit/$") & custom_filters.admin_only,
)
async def edit_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    menu.add_row_button("Название", "alias")
    menu.add_row_button("Категорию", "nc")
    menu.add_row_button(
        "Режим",
        ":off_rewrite" if source_obj.is_rewrite else ":on_rewrite",
    )

    last_text = []
    if source_obj.title_alias:
        last_text.append(f"Название: **{source_obj.title_alias}**")
    last_text.append(
        "Режим перепечатывания: " + ("✅" if source_obj.is_rewrite else "📴")
    )

    await callback_query.message.edit_text(
        text=await menu.get_text(
            source_obj=source_obj,
            last_text="\n".join(last_text) + "\n\nЧто ты хочешь изменить?",
        ),
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
