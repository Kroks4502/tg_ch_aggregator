import pickle

import settings
from plugins.user.types import Operation


def dump_message(message, operation: Operation) -> None:
    """Дамп экземпляров сообщений для сбора тестовых данных."""
    if settings.DUMP_MESSAGE_MODE:
        directory = settings.DUMP_MESSAGES_DIRS_BY_OPERATION.get(operation)
        chat_id = getattr(message, "chat_id", None) or getattr(message, "id", "unknown")
        msg_id = getattr(message, "id", "unknown")
        filename = f"{chat_id}_{msg_id}"
        with open(directory / filename, "wb") as file:
            pickle.dump(message, file)
