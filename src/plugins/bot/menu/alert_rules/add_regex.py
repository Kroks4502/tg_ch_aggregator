from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from models import AlertRule
from plugins.bot.constants import CANCEL, INVALID_PATTERN_TEXT
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r"/c/-\d+/r/:add/regex/$") & custom_filters.admin_only,
)
async def add_regex_alert_rule(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        "ОК. Ты добавляешь новое правило уведомления.\n\n"
        f"**Введи регулярное выражение** или {CANCEL}"
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        add_regex_alert_rule_waiting_input,
        client,
        callback_query,
    )


async def add_regex_alert_rule_waiting_input(
    _,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data, back_step=2)

    category_id = menu.path.get_value("c")

    async def reply(t):
        await message.reply_text(
            text=t,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    pattern = str(message.text)
    if not is_valid_pattern(pattern):
        await reply(INVALID_PATTERN_TEXT)
        return

    AlertRule.create(
        user_id=message.from_user.id,
        category_id=category_id,
        type="regex",
        config=dict(regex=pattern),
    )

    text = (
        "✅ Правило уведомления о сообщениях соответствующих регулярному выражению"
        f" `{pattern}` добавлен"
    )
    await reply(text)
