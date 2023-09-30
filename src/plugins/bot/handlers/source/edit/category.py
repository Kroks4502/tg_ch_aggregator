from peewee import JOIN, fn

from models import Category, Source
from plugins.bot import router
from plugins.bot.handlers.source.common.constants import (
    QUESTION_SELECT_NEW_CATEGORY,
    SINGULAR_SOURCE_TITLE,
)
from plugins.bot.handlers.source.common.utils import (
    get_source_menu_success_text,
    get_source_menu_text,
)
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
        .where(Category.id != source_obj.category_id)
        .group_by(Category.id)
    )
    menu.add_rows_from_data(
        data=[ButtonData(i.title, i.id, i.amount) for i in query],
    )

    return await get_source_menu_text(
        title=SINGULAR_SOURCE_TITLE,
        source_id=source_id,
        category_id=source_obj.category_id,
        alias=source_obj.title_alias,
        is_rewrite=source_obj.is_rewrite,
        question=QUESTION_SELECT_NEW_CATEGORY,
    )


@router.page(path=r"/s/-\d+/:edit/nc/-\d+/", send_to_admins=True, back_step=2)
async def set_source_category(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj = Source.get(source_id)

    new_category_id = menu.path.get_value("nc")

    source_obj.category = new_category_id
    source_obj.save()

    menu.path.set_value("c", new_category_id)

    cat_link = await get_channel_formatted_link(new_category_id)
    return await get_source_menu_success_text(
        source_id=source_id,
        action=f"перенесен в категорию **{cat_link}**",
    )
