import pickle

import settings
from common.types import MessageEventType
from plugins.user.types import Operation


def dump_message(event: MessageEventType, operation: Operation) -> None:
    """Дамп экземпляров сообщений для сбора тестовых данных."""
    if settings.DUMP_MESSAGE_MODE:
        directory = settings.DUMP_MESSAGES_DIRS_BY_OPERATION.get(operation)
        filename = f"{event.chat_id}_{event.id}"
        with open(directory / filename, "wb") as file:
            pickle.dump(event, file)
