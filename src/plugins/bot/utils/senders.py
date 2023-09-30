import logging

from pyrogram import Client, types
from pyrogram.errors import RPCError

from models import User


async def send_message_to_admins(
    client: Client,
    user: types.User,
    text: str,
) -> None:
    """Отправка сообщений всем администраторам бота."""
    admins = User.select(User.id).where((User.id != user.id) & User.is_admin == True)
    for admin in admins:
        try:
            await client.send_message(
                admin.id,
                f"{get_username(user)}\n{text}",
                disable_web_page_preview=True,
            )
        except RPCError as e:
            logging.error(e, exc_info=True)


def get_username(user: types.User) -> str:
    """Получить имя пользователя для сообщения администраторам."""
    if user.username:
        return f"@{user.username}"

    full_name = (
        f'{user.first_name + " " if user.first_name else ""}'
        f'{user.last_name if user.last_name else ""}'
    )
    return f"{full_name} ({user.id})" if full_name else f"{user.id}"
