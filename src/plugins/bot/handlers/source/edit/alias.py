from pyrogram.types import Message

from models import Source
from plugins.bot import router, validators
from plugins.bot.constants.settings import MAX_LENGTH_SOURCE_ALIAS
from plugins.bot.handlers.source.common.constants import ACTION_ENTER_SOURCE_ALIAS
from plugins.bot.handlers.source.common.utils import (
    get_dialog_text,
    get_source_menu_success_text,
)
from plugins.bot.menu import Menu


@router.wait_input(send_to_admins=True)
async def edit_alias_waiting_input(
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, MAX_LENGTH_SOURCE_ALIAS)

    source_id = menu.path.get_value("s")
    source_obj = Source.get(
        id=source_id,
        is_deleted=False,
    )

    if message.text == source_obj.title:
        source_obj.title_alias = None
        action = "получил оригинальное название"
    else:
        source_obj.title_alias = message.text
        action = f"получил псевдоним **{source_obj.title_alias}**"
    source_obj.save()

    return await get_source_menu_success_text(source_id=source_id, action=action)


@router.page(
    path=r"/s/-\d+/:edit/alias/",
    reply=True,
    add_wait_for_input=edit_alias_waiting_input,
)
async def edit_alias(menu: Menu):
    return await get_dialog_text(
        category_id=menu.path.get_value("c"),
        source_id=menu.path.get_value("s"),
        doing="задаёшь псевдоним",
        action=ACTION_ENTER_SOURCE_ALIAS,
    )
