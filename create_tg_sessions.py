import sys
from pathlib import Path

src_path = str(Path(__file__).parent / 'src')
try:
    sys.path.index(src_path)
except ValueError:
    sys.path.append(src_path)

from clients import bot, user  # noqa: E402

if __name__ == '__main__':

    async def create_sessions():
        """
        Создать сессии и отправить сообщение от имени бота пользователю.
        При создании сессии нужно будет пройти авторизацию.
        Для отправки сообщения пользователь уже должен был общаться с ботом.
        """
        bot.plugins = None
        user.plugins = None
        async with bot, user:
            bot_info = await bot.get_me()
            user_info = await user.get_me()
            await bot.send_message(
                chat_id=user_info.id,
                text=(
                    f'Сессии пользователя `{user_info.id}` (`{user_info.username}`) '
                    f'и бота `{bot_info.id}` (`{bot_info.username}`) актуальны'
                ),
            )

    user.run(create_sessions())
