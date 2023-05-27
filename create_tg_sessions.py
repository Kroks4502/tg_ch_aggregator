from clients import bot, user


async def create_sessions():
    """
    Создать сессии и отправить сообщение от имени бота пользователю.
    При создании сессии нужно будет пройти авторизацию.
    Для отправки сообщения пользователь уже должен был общаться с ботом.
    """
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


if __name__ == '__main__':
    user.run(create_sessions())
