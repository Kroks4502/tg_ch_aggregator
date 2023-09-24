from models import Source
from plugins.bot import router
from plugins.bot.menu import Menu
from plugins.bot.utils.chat_info import get_chat_info


@router.page(path=r"/s/-\d+/")
async def detail_source(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    last_text = []
    if menu.is_admin_user():
        menu.add_button.row_edit_delete()

        menu.add_button.messages_histories()

        menu.add_button.filters(source_id=source_obj.id)

        menu.add_button.statistics()

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

    return await menu.get_text(source_obj=source_obj, last_text="\n".join(last_text))
