from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from models import AlertRule
from plugins.bot.constants import CANCEL, INVALID_PATTERN_TEXT
from plugins.bot.menu import Menu
from plugins.bot.utils import custom_filters
from plugins.bot.utils.checks import is_valid_pattern
from plugins.bot.utils.managers import input_wait_manager
from utils.menu.path import Path


@Client.on_callback_query(
    filters.regex(r"/r/\d+/:edit/$") & custom_filters.admin_only,
)
async def edit_regex_alert_rule(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()

    path = Path(callback_query.data)
    rule_id = path.get_value("r")
    rule_obj = AlertRule.get(rule_id)

    await callback_query.message.reply(
        f"ОК. Ты изменяешь правило уведомления `{rule_obj.config['regex']}`.\n\n"
        f"**Введи регулярное выражение** или {CANCEL}"
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        edit_regex_alert_rule_waiting_input,
        client,
        callback_query,
    )


async def edit_regex_alert_rule_waiting_input(
    _,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data)

    rule_id = menu.path.get_value("r")
    rule_obj = AlertRule.get(rule_id)

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

    old_pattern = rule_obj.config["regex"]
    rule_obj.config["regex"] = pattern
    rule_obj.save()

    text = (
        "✅ Правило уведомления о сообщениях соответствующих регулярному выражению"
        f" изменено c `{old_pattern}` на `{pattern}`"
    )
    await reply(text)
