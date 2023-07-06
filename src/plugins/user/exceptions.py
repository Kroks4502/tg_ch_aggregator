import logging
from enum import Enum

from pyrogram.enums import ChatType
from pyrogram.types import Chat, Message

from plugins.user.utils.chats_locks import MessagesLocks


class Operation(Enum):
    NEW = "отправил"
    EDIT = "изменил"
    DELETE = "удалил"


class UserBaseError(Exception):
    pass


class MessageBaseError(UserBaseError):
    stack_info = False
    exc_info = None
    logging_level = logging.INFO
    start_tmpl = "Источник {source_id} {operation} сообщение {message_id}"
    end_tmpl = ""

    def __init__(self, operation: Operation, message: Message, **kwargs):
        self.message = message
        self.operation = operation
        self.text = self.generate_exc_text(**kwargs)
        logging.log(
            level=self.logging_level,
            msg=f'{self.__class__.__name__} : {self.text}',
            exc_info=self.exc_info,
            stack_info=self.stack_info,
        )

    def generate_exc_text(self, **kwargs):
        start_text = self.start_tmpl.format(
            source_id=self.message.chat.id,
            operation=self.operation.value,
            message_id=self.message.id,
        )
        end_text = self.end_tmpl.format(**kwargs)

        if not end_text:
            return f'{start_text}.'

        return f'{start_text}, {end_text}.'

    def __str__(self):
        return self.text


class MessageBlockedByMediaGroupError(MessageBaseError):
    """Сообщение было ранее заблокировано по message.media_group_id."""

    logging_level = logging.WARNING
    end_tmpl = 'но медиа группа {media_group_id} уже заблокирована {blocked}'

    def __init__(self, operation: Operation, message: Message, blocked: MessagesLocks):
        super().__init__(
            operation=operation,
            message=message,
            media_group_id=message.media_group_id,
            blocked=blocked,
        )


class MessageBlockedByIdError(MessageBaseError):
    """Сообщение было ранее заблокировано по message.id."""

    logging_level = logging.WARNING
    end_tmpl = 'но оно уже заблокировано {blocked}'

    def __init__(self, operation: Operation, message: Message, blocked: MessagesLocks):
        super().__init__(operation=operation, message=message, blocked=blocked)


class MessageNotFoundOnHistoryError(MessageBaseError):
    """Сообщения нет в истории."""

    logging_level = logging.WARNING
    end_tmpl = 'его нет в истории'


class MessageNotOnCategoryError(MessageBaseError):
    """Сообщение не публиковалось в категории."""

    end_tmpl = 'оно не публиковалось в категории'


class MessageNotRewrittenError(MessageBaseError):
    """Сообщение нельзя отредактировать."""

    end_tmpl = (
        'оно не может быть изменено в категории, '
        'потому что было переслано и не перепечатывалось'
    )


class MessageNotModifiedError(MessageBaseError):
    """Сообщение не удалось перепечатать."""

    end_tmpl = 'перепечатать сообщение в категории не удалось {error}'

    def __init__(self, operation: Operation, message: Message, error):
        super().__init__(operation=operation, message=message, error=error)


class MessageRepeatedError(MessageBaseError):
    """Сообщение уже опубликовано в категории."""

    end_tmpl = 'оно уже опубликовано в категории'


class MessageFilteredError(MessageBaseError):
    """Сообщение не прошло фильтрацию."""

    end_tmpl = 'оно было отфильтровано'


class MessageMediaWithoutCaptionError(MessageBaseError):
    """Сообщение не может содержать подпись."""

    end_tmpl = 'но оно не может содержать подпись'


class MessageIdInvalidError(MessageBaseError):
    """Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника."""

    logging_level = logging.WARNING
    end_tmpl = 'оно привело к ошибке {error}'

    def __init__(self, operation: Operation, message: Message, error):
        super().__init__(operation=operation, message=message, error=error)


class MessageForwardsRestrictedError(MessageBaseError):
    """Сообщение запрещено пересылать."""

    logging_level = logging.ERROR
    end_tmpl = 'но запрещает пересылку сообщений'


class MessageTooLongError(MessageBaseError):
    """Сообщение содержит слишком длинный текст."""

    logging_level = logging.ERROR
    end_tmpl = 'но при перепечатывании оно превышает лимит знаков'


class MessageBadRequestError(MessageBaseError):
    """Сообщение привело к непредвиденной ошибке."""

    stack_info = True
    logging_level = logging.ERROR
    end_tmpl = 'оно привело к непредвиденной ошибке {error}'

    def __init__(self, operation: Operation, message: Message, error):
        super().__init__(operation=operation, message=message, error=error)
        self.exc_info = error


if __name__ == "__main__":
    raise MessageMediaWithoutCaptionError(
        Operation.NEW, Message(id=0, chat=Chat(id=0, type=ChatType.CHANNEL))
    )
