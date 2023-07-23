import pickle

from pyrogram.types import Message

import config
from plugins.user.types import Operation


def dump_message(message: Message, operation: Operation) -> None:
    """Дамп экземпляров сообщений для сбора тестовых данных."""
    if config.DUMP_MESSAGE_MODE:
        directory = config.DUMP_MESSAGES_DIRS_BY_OPERATION.get(operation)
        filename = f"{message.chat.id}_{message.id}"
        with open(directory / filename, 'wb') as file:
            pickle.dump(message, file)
