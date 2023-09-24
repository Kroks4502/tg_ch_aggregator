from models import Source
from plugins.bot import router
from plugins.bot.menu import Menu


@router.page(path=r"/s/-\d+/:edit/")
async def edit_source(menu: Menu):
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

    return await menu.get_text(
        source_obj=source_obj,
        last_text="\n".join(last_text) + "\n\nЧто ты хочешь изменить?",
    )
