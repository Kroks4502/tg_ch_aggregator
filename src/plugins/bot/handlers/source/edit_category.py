from peewee import JOIN, fn

from models import Category, Source
from plugins.bot import router
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link
from utils.menu import ButtonData


@router.page(path=r"/s/-\d+/:edit/nc/")
async def edit_source_category(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj: Source = Source.get(source_id)

    query = (
        Category.select(
            Category.id,
            Category.title,
            fn.Count(Source.id).alias("amount"),
        )
        .join(Source, JOIN.LEFT_OUTER)
        .group_by(Category.id)
    )
    menu.add_rows_from_data(
        data=[ButtonData(i.title, i.id, i.amount) for i in query],
    )

    return await menu.get_text(
        source_obj=source_obj,
        last_text="Ты **меняешь категорию** у источника.\nВыбери новую категорию:",
    )


@router.page(path=r"/s/-\d+/:edit/nc/-\d+/", send_to_admins=True, back_step=2)
async def set_source_category(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj = Source.get(source_id)

    old_category_obj = source_obj.category

    new_category_id = menu.path.get_value("nc")
    new_category_obj = Category.get(new_category_id)

    source_obj.category = new_category_obj
    source_obj.save()

    menu.path.set_value("с", new_category_id)

    src_link = await get_channel_formatted_link(source_obj.id)
    cat_link_old = await get_channel_formatted_link(old_category_obj.id)
    cat_link_new = await get_channel_formatted_link(new_category_obj.id)
    return (
        f"✅ Категория источника **{src_link}** изменена с **{cat_link_old}** на"
        f" **{cat_link_new}**"
    )
