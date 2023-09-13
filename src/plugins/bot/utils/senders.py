import logging

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import CallbackQuery

from models import User


async def send_message_to_admins(
    client: Client,
    callback_query: CallbackQuery,
    text: str,
):
    """Отправка сообщений всем администраторам бота."""
    f_user = callback_query.from_user
    for admin_tg_id in User.get_cache_admins_tg_ids() - {f_user.id}:
        if f_user.username:
            b_text = f'@{f_user.username}'
        else:
            full_name = (
                f'{f_user.first_name + " " if f_user.first_name else ""}'
                f'{f_user.last_name if f_user.last_name else ""}'
            )
            b_text = f'{full_name} ({f_user.id})' if full_name else f'{f_user.id}'
        try:
            await client.send_message(
                admin_tg_id,
                f'{b_text}\n{text}',
                disable_web_page_preview=True,
            )
        except RPCError as e:
            logging.error(e, exc_info=True)
