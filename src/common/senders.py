import logging

from pyrogram import Client
from pyrogram.errors import RPCError
from pyrogram.types import (
    ForceReply,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from models import User


async def send_message_to_admins(
    client: Client,
    text: str,
    reply_markup: InlineKeyboardMarkup
    | ReplyKeyboardMarkup
    | ReplyKeyboardRemove
    | ForceReply
    | None = None,
    except_user_id: int = None,
) -> None:
    """
    Отправить сообщение всем администраторам бота.

    :param client: Клиент для отправки сообщения.
    :param text: Текст сообщения.
    :param except_user_id: Исключить отправку пользователю.
    :param reply_markup: Дополнительные возможности разметки сообщения.
    """
    admins = User.select(User.id).where(
        (User.is_admin == True) & (User.id != except_user_id)
    )
    for admin in admins:
        try:
            await client.send_message(
                chat_id=admin.id,
                text=text,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
            )
        except RPCError as e:
            logging.error(e, exc_info=True)
