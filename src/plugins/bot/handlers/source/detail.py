from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import MessageHistory, Source
from plugins.bot.menu import Menu
from plugins.bot.utils.chat_info import get_chat_info
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.statistic import get_statistic_text


@Client.on_callback_query(
    filters.regex(r"/s/-\d+/$"),
)
async def detail_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    last_text = []
    if is_admin(callback_query.from_user.id):
        menu.add_button.row_edit_delete()

        menu.add_button.messages_histories()

        menu.add_button.filters(source_id=source_obj.id)

        if source_obj.is_rewrite:
            menu.add_button.cleanups(amount=len(source_obj.cleanup_list))

        chat_info = await get_chat_info(source_obj)
        if chat_info:
            last_text.append(f"{chat_info}\n")

    if source_obj.title_alias:
        last_text.append(f"Название: **{source_obj.title_alias}**")

    last_text.append(
        "Режим перепечатывания: " + ("✅" if source_obj.is_rewrite else "📴")
    )

    statistic_text = get_statistic_text(where=MessageHistory.source == source_obj)
    last_text.append(f"\n{statistic_text}")

    text = await menu.get_text(source_obj=source_obj, last_text="\n".join(last_text))
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
