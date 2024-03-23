import asyncio
import sys
from pathlib import Path

src_path = str(Path(__file__).parent / "src")
try:
    sys.path.index(src_path)
except ValueError:
    sys.path.append(src_path)

from clients import bot_client, user_client  # noqa: E402

SUCCESS_MESSAGE_TEXT = (
    "Сессии актуальны: \n"
    "– user: `{user_id}` (`{user_username}`)\n"
    "– bot: `{bot_id}` (`{bot_username}`)"
)


async def create_sessions():
    """
    Создать сессии и отправить сообщение от имени бота пользователю.
    При создании сессии необходимо пройти аутентификацию.
    Для успешной отправки сообщения пользователь уже должен был написать сообщение боту.
    """
    user = await user_client.get_me()
    bot = await bot_client.get_me()

    text = SUCCESS_MESSAGE_TEXT.format(
        user_id=user.id,
        user_username=user.username,
        bot_id=bot.id,
        bot_username=bot.username,
    )
    await bot_client.send_message(
        entity=user.id,
        message=text,
    )
    print(text)  # noqa: T201


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_sessions())
