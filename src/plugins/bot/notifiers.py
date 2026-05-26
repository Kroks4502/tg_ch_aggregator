"""
In-process реализации notifier-контрактов поверх aiogram.Bot.

На этапе 2 (Telethon + разделение процессов) эти классы заменяются на
OutboxImpl, который пишет в `notification_outbox`-таблицу. Контракты
(AdminNotifier / UserErrorNotifier / AlertNotifier) и DTO остаются те же.
"""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from clients import aiogram_bot
from common.dto import AdminNotification, AlertNotification
from common.menu_paths import ALERT_DETAIL_PATH
from models import User
from plugins.bot.text_formatter import pyrogram_markdown_to_html


def _to_aiogram_markup(
    notification: AdminNotification,
) -> InlineKeyboardMarkup | None:
    if not notification.button_rows:
        return None
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=btn.text, callback_data=btn.callback_data)
                for btn in row.buttons
            ]
            for row in notification.button_rows
        ]
    )


async def _send_to_one(bot: Bot, chat_id: int, **kwargs) -> None:
    # Тексты пишутся под pyrogram-Markdown — конвертируем в HTML, потому что
    # aiogram_bot создан с parse_mode=HTML (см. clients.py).
    if "text" in kwargs:
        kwargs["text"] = pyrogram_markdown_to_html(kwargs["text"])
    try:
        await bot.send_message(chat_id=chat_id, disable_web_page_preview=True, **kwargs)
    except TelegramAPIError as exc:
        logging.error("send_message to %s failed: %s", chat_id, exc, exc_info=True)


class _InProcessAdminNotifier:
    async def notify(self, notification: AdminNotification) -> None:
        markup = _to_aiogram_markup(notification)
        admins = User.select(User.id).where(
            (User.is_admin == True) & (User.id != notification.except_user_id)
        )
        for admin in admins:
            await _send_to_one(
                aiogram_bot,
                admin.id,
                text=notification.text,
                reply_markup=markup,
            )


class _InProcessUserErrorNotifier:
    async def report(self, text: str) -> None:
        admins = User.select(User.id).where(User.is_admin == True)
        for admin in admins:
            await _send_to_one(aiogram_bot, admin.id, text=text)


class _InProcessAlertNotifier:
    async def alert(self, notification: AlertNotification) -> None:
        # Импорт внутри метода — handler-модуль регистрирует @router.page
        # декораторы при импорте, и для них нужен полностью инициализированный
        # plugins.bot. Lazy-import избегает циклов.
        from plugins.bot.handlers.alert_rules.alert.detail import render_alert_view
        from plugins.bot.menu import Menu

        path = ALERT_DETAIL_PATH.format(alert_id=notification.alert_id) + "?new"
        menu = Menu(
            path=path,
            user_id=notification.user_id,
        )

        try:
            text = await render_alert_view(menu, alert_id=notification.alert_id)
        except Exception:
            logging.exception(
                "render_alert_view failed for alert %s", notification.alert_id
            )
            return

        if not text:
            return

        await _send_to_one(
            aiogram_bot,
            notification.user_id,
            text=text,
            reply_markup=menu.reply_markup,
        )


admin_notifier = _InProcessAdminNotifier()
user_error_notifier = _InProcessUserErrorNotifier()
alert_notifier = _InProcessAlertNotifier()
