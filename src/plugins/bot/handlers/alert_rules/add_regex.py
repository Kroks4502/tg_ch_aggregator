from pyrogram.types import Message

from models import AlertRule
from plugins.bot import router, validators
from plugins.bot.constants import CANCEL
from plugins.bot.menu import Menu


@router.wait_input(back_step=2)
async def add_regex_alert_rule_waiting_input(
    message: Message,
    menu: Menu,
):
    pattern = str(message.text)
    validators.is_valid_pattern(pattern)

    category_id = menu.path.get_value("c")
    AlertRule.create(
        user_id=message.from_user.id,
        category_id=category_id,
        type="regex",
        config=dict(regex=pattern),
    )

    return (
        "✅ Правило уведомления о сообщениях соответствующих регулярному выражению"
        f" `{pattern}` добавлен"
    )


@router.page(
    path=r"/r/:add/regex/",
    reply=True,
    add_wait_for_input=add_regex_alert_rule_waiting_input,
)
async def add_regex_alert_rule():
    return (
        "ОК. Ты добавляешь новое правило уведомления.\n\n"
        f"**Введи регулярное выражение** или {CANCEL}"
    )
