import logging
from typing import Callable

from pyrogram import Client
from pyrogram.handlers import MessageHandler
from pyrogram.types import Message

from plugins.bot.menu import custom_filters


class InputWaitManager:
    """Менеджер ожидания отправки пользователем сообщения боту."""

    _waiting_chats: dict[int : dict[str:any]] = {}

    def add(
        self,
        chat_id: int,
        func: Callable[[Client, Message, any], None],
        client: Client,
        *args,
        **kwargs,
    ) -> None:
        self._waiting_chats[chat_id] = {
            'handler': client.add_handler(
                MessageHandler(
                    self.__input_text,
                    filters=(
                        custom_filters.chat(chat_id) & ~custom_filters.command_message
                    ),
                ),
            ),
            'func': func,
            'args': args,
            'kwargs': kwargs,
        }

    def remove(
        self,
        client,
        chat_id,
    ) -> dict[str]:
        input_chat = self._waiting_chats.pop(chat_id)
        client.remove_handler(*input_chat['handler'])
        return input_chat

    async def __input_text(
        self,
        client: Client,
        message: Message,
    ) -> None:
        input_chat = self.remove(client, message.chat.id)
        try:
            await input_chat['func'](
                client, message, *input_chat['args'], **input_chat['kwargs']
            )
        except Exception as e:
            msg = (
                'Во время выполнения функции '
                f'{input_chat["func"].__name__} '
                'было перехвачено исключение'
            )
            logging.error(f'{msg}: {e}', exc_info=True)
            await message.reply(f'❌ {msg}:\n{e}')


input_wait_manager = InputWaitManager()
