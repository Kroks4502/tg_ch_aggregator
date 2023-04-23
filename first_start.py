from clients import user, bot
from models import Category, Source, Filter, Admin, FilterMessageHistory, CategoryMessageHistory
from settings import DATABASE


if __name__ == '__main__':
    # Создаем таблицы в БД
    DATABASE.create_tables(
        [
            Category, Source, Filter, Admin,
            FilterMessageHistory, CategoryMessageHistory
        ]
    )

    async def create_sessions():
        async with bot, user:
            bot_info = await bot.get_me()
            user_info = await user.get_me()
            await user.send_message(
                chat_id='me',
                text=f'Сессии пользователя `{user_info.id}` (`{user_info.username}`) '
                     f'и бота `{bot_info.id}` (`{bot_info.username}`) актуальны'
            )

    user.run(create_sessions())
