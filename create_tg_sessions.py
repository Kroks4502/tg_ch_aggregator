import sys
from pathlib import Path

src_path = str(Path(__file__).parent / "src")
try:
    sys.path.index(src_path)
except ValueError:
    sys.path.append(src_path)

from clients import bot_client, user_client  # noqa: E402

SUCCESS_MESSAGE_TEXT = (
    "Сессии пользователя `{user_id}` (`{user_username}`) "
    "и бота `{bot_id}` (`{bot_username}`) актуальны"
)


if __name__ == "__main__":

    async def create_sessions():
        """
        Создать сессии и отправить сообщение от имени бота пользователю.
        При создании сессии нужно будет пройти авторизацию.
        Для отправки сообщения пользователь уже должен был общаться с ботом.
        """
        bot_client.plugins = None
        user_client.plugins = None
        async with bot_client, user_client:
            bot_info = await bot_client.get_me()
            user_info = await user_client.get_me()
            text = SUCCESS_MESSAGE_TEXT.format(
                user_id=user_info.id,
                user_username=user_info.username,
                bot_id=bot_info.id,
                bot_username=bot_info.username,
            )
            await bot_client.send_message(
                chat_id=user_info.id,
                text=text,
            )
        print(text)  # noqa: T201

    user_client.run(create_sessions())
