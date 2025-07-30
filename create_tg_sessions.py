from clients import bot_client, user_client  # noqa: E402

SUCCESS_MESSAGE_TEXT = (
    "Sessions for Telegram user `{user_id}` (`{user_username}`) "
    "and bot `{bot_id}` (`{bot_username}`) are valid"
)


async def create_sessions():
    """
    Create sessions and send message from bot to user.

    [!] For sending a message, the user must already have been talking to the bot.
    [!] When creating a session, you need to go through authorization.
    """
    bot_client.plugins = None
    user_client.plugins = None

    print("\033[93m[bot_client]: Initialize Telegram bot client\033[0m")
    async with bot_client:
        print("\033[93m[bot_client]: Get bot info\033[0m")
        bot_info = await bot_client.get_me()
        print(bot_info)

        print("\033[93m[user_client]: Initialize Telegram user client\033[0m")
        async with user_client:
            print("\033[93m[user_client]: Get user info\033[0m")
            user_info = await user_client.get_me()
            print(user_info)

            print("\033[93m[bot_client]: Send message to user_client\033[0m")
            message_text = SUCCESS_MESSAGE_TEXT.format(
                user_id=user_info.id,
                user_username=user_info.username,
                bot_id=bot_info.id,
                bot_username=bot_info.username,
            )
            await bot_client.send_message(
                chat_id=user_info.id,
                text=message_text,
            )
    print(f"\033[92m{message_text}\033[0m")  # noqa: T201


if __name__ == "__main__":
    user_client.run(create_sessions())
