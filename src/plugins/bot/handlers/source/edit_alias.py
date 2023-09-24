from pyrogram.types import Message

from models import Source
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link

REWRITE_TEXT_TPL = "✅ Установлен режим {} сообщений для источника {}"


@router.wait_input(send_to_admins=True)
async def edit_alias_waiting_input(
    message: Message,
    menu: Menu,
):
    validators.is_text(message)
    validators.text_length_less_than(message, 100)

    source_id = menu.path.get_value("s")
    source_obj = Source.get(source_id)

    src_link = await get_channel_formatted_link(source_obj.id)

    if message.text == source_obj.title:
        source_obj.title_alias = None
        source_obj.save()
        return f"✅ Источник **{src_link}** получил оригинальное название"

    source_obj.title_alias = message.text
    source_obj.save()
    return f"✅ Источник **{src_link}** получил название **{source_obj.title_alias}**"


@router.page(
    path=r"/s/-\d+/:edit/alias/",
    reply=True,
    add_wait_for_input=edit_alias_waiting_input,
)
async def edit_alias(menu: Menu):
    source_id = menu.path.get_value("s")
    source_obj = Source.get(source_id)

    return (
        f"ОК. Ты меняешь название для источника `{source_obj.title}`.\n\n"
        f"**Введи новое** или {CANCEL}"
    )
