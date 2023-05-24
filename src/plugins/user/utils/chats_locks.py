import logging


class ChatsLocks:
    def __init__(self, name: str):
        self.__chats = {}
        self.__name = name

    class __MessagesLocks:
        def __init__(self, name: str, chat_id, chat: set):
            self.__name = name
            self.__chat_id = chat_id
            self.__chat = chat

        def add(self, value):
            logging.info(f'Добавлена блокировка {self.__name} для чата {self.__chat_id} {value}')
            self.__chat.add(value)

        def remove(self, value):
            try:
                logging.info(f'Снята блокировка {self.__name} для чата {self.__chat_id} {value}')
                self.__chat.remove(value)
            except KeyError:
                logging.warning(f'Не удалось снять блокировку {self.__name} для чата '
                                f'{self.__chat_id} со значением {value}. '
                                f'Текущие блокировки: {self.__chat}')

        def contains(self, key) -> bool:
            return key in self.__chat

    def get(self, key):
        if not (messages := self.__chats.get(key)):
            messages = self.__chats[key] = set()
            self.__optimize()
        return self.__MessagesLocks(self.__name, key, messages)

    def __optimize(self):
        if len(self.__chats) > 5:
            self.__chats.pop(list(self.__chats.keys())[0])
