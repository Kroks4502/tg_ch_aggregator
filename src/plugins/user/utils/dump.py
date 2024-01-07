import pickle

from pyrogram.types import Message

import settings
from plugins.user.types import Operation


def dump_message(message: Message, operation: Operation) -> None:
    """Дамп экземпляров сообщений для сбора тестовых данных."""
    if settings.DUMP_MESSAGE_MODE:
        directory = settings.DUMP_MESSAGES_DIRS_BY_OPERATION.get(operation)
        filename = f"{message.chat.id}_{message.id}"
        with open(directory / filename, "wb") as file:
            pickle.dump(message, file)
