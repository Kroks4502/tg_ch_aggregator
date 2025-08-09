import logging


class ChatsLocks:
    def __init__(self, name: str):
        self.__chats = {}
        self.__name = name

    def get(self, key):
        if key not in self.__chats:
            self.__chats[key] = set()
            self.__optimize()
        return MessagesLocks(self.__name, key, self.__chats[key])

    def __optimize(self):
        if len(self.__chats) > 5:
            oldest_key = next(iter(self.__chats))
            self.__chats.pop(oldest_key, None)

    def __str__(self):
        return str(self.__chats)


class MessagesLocks:
    def __init__(self, name: str, chat_id, chat: set):
        self.__name = name
        self.__chat_id = chat_id
        self.__chat = chat

    def add(self, value):
        logging.info(
            "Добавлена блокировка %s для чата %s %s",
            self.__name,
            self.__chat_id,
            value,
        )
        self.__chat.add(value)

    def remove(self, value):
        try:
            logging.info(
                "Снята блокировка %s для чата %s %s",
                self.__name,
                self.__chat_id,
                value,
            )
            self.__chat.remove(value)
        except KeyError:
            logging.warning(
                (
                    "Не удалось снять блокировку %s для чата %s со значением %s."
                    " Текущие блокировки: %s"
                ),
                self.__name,
                self.__chat_id,
                value,
                self.__chat,
            )

    def contains(self, key) -> bool:
        return key in self.__chat

    def __len__(self):
        return len(self.__chat)

    def __str__(self):
        return str(self.__chat)
