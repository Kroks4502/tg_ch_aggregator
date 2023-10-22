import logging
from enum import Enum

from pyrogram import errors as pyrogram_errors
from pyrogram.types import Message

from plugins.user.utils.chats_locks import MessagesLocks
from settings import APP_START_DATETIME


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
    include_message = False

    def __init__(self, operation: Operation, message: Message, **kwargs):
        self.message = message
        self.operation = operation
        self.text = self.generate_exc_text(**kwargs)
        self.kwargs = kwargs
        logging.log(
            level=self.logging_level,
            msg=f"{self.__class__.__name__} : {self.text}",
            exc_info=self.exc_info,
            stack_info=self.stack_info,
        )

    def generate_exc_text(self, **kwargs):
        start_text = self.start_tmpl.format(
            source_id=self.message.chat.id,
            operation=self.operation.value,
            message_id=self.message.id,
        )

        text_items = [start_text]
        if end_text := self.end_tmpl.format(**kwargs):
            text_items.append(end_text)
        if self.include_message:
            text_items.append(f"message={self.message}")

        return f"{', '.join(text_items)}."

    def to_dict(self):
        return dict(
            name=self.__class__.__name__,
            text=self.text,
            operation=self.operation.name,
            kwargs=str(self.kwargs),
        )

    def __str__(self):
        return self.text


class MessageBlockedByMediaGroupError(MessageBaseError):
    """Сообщение было ранее заблокировано по message.media_group_id."""

    end_tmpl = "но медиа группа {media_group_id} уже заблокирована {blocked}"

    def __init__(self, operation: Operation, message: Message, blocked: MessagesLocks):
        super().__init__(
            operation=operation,
            message=message,
            media_group_id=message.media_group_id,
            blocked=blocked,
        )


class MessageBlockedByIdError(MessageBaseError):
    """Сообщение было ранее заблокировано по message.id."""

    end_tmpl = "но оно уже заблокировано {blocked}"

    def __init__(self, operation: Operation, message: Message, blocked: MessagesLocks):
        super().__init__(operation=operation, message=message, blocked=blocked)


class MessageNotFoundOnHistoryError(MessageBaseError):
    """Сообщения нет в истории."""

    logging_level = logging.WARNING
    end_tmpl = "его нет в истории date={date}, edit_date={edit_date}"

    def __init__(self, operation: Operation, message: Message):
        if (
            message.date
            and message.edit_date
            and (
                (message.edit_date - message.date).total_seconds() < 10
                or APP_START_DATETIME > message.date
            )
            or (not message.date and operation == Operation.DELETE)
        ):
            self.logging_level = logging.INFO

        if not message.date and operation != Operation.DELETE:
            self.include_message = True

        super().__init__(
            operation=operation,
            message=message,
            date=message.date,
            edit_date=message.edit_date,
        )


class MessageNotOnCategoryError(MessageBaseError):
    """Сообщение не публиковалось в категории."""

    end_tmpl = "оно не публиковалось в категории"


class MessageNotRewrittenError(MessageBaseError):
    """Сообщение нельзя отредактировать."""

    end_tmpl = (
        "оно не может быть изменено в категории, "
        "потому что было переслано и не перепечатывалось"
    )


class MessageNotModifiedError(MessageBaseError):
    """Сообщение не удалось перепечатать."""

    end_tmpl = "перепечатать сообщение в категории не удалось {error}"

    def __init__(
        self,
        operation: Operation,
        message: Message,
        error: pyrogram_errors.MessageNotModified,
    ):
        super().__init__(operation=operation, message=message, error=error)


class MessageRepeatedError(MessageBaseError):
    """Сообщение уже опубликовано в категории."""

    end_tmpl = "оно уже опубликовано в категории"


class MessageFilteredError(MessageBaseError):
    """Сообщение не прошло фильтрацию."""

    end_tmpl = "оно было отфильтровано"


class MessageMediaWithoutCaptionError(MessageBaseError):
    """Сообщение не может содержать подпись."""

    end_tmpl = "но оно не может содержать подпись"


class MessageIdInvalidError(MessageBaseError):
    """Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника."""

    logging_level = logging.WARNING
    end_tmpl = "оно привело к ошибке {error}"

    def __init__(
        self,
        operation: Operation,
        message: Message,
        error: pyrogram_errors.MessageIdInvalid,
    ):
        super().__init__(operation=operation, message=message, error=error)


class MessageForwardsRestrictedError(MessageBaseError):
    """Сообщение запрещено пересылать."""

    logging_level = logging.WARNING
    end_tmpl = "но запрещает пересылку сообщений"


class MessageTooLongError(MessageBaseError):
    """Сообщение содержит слишком длинный текст."""

    logging_level = logging.ERROR
    end_tmpl = "но при перепечатывании оно превышает лимит знаков {error}"

    def __init__(
        self,
        operation: Operation,
        message: Message,
        error: pyrogram_errors.MediaCaptionTooLong | pyrogram_errors.MessageTooLong,
    ):
        super().__init__(operation=operation, message=message, error=error)


class MessageBadRequestError(MessageBaseError):
    """Сообщение привело к необработанной ошибке при запросе."""

    logging_level = logging.ERROR
    end_tmpl = "оно привело к необработанной ошибке при запросе {error}"

    def __init__(
        self,
        operation: Operation,
        message: Message,
        error: pyrogram_errors.BadRequest,
    ):
        super().__init__(operation=operation, message=message, error=error)


class MessageUnknownError(MessageBaseError):
    """Сообщение привело к неизвестной ошибке."""

    logging_level = logging.ERROR
    end_tmpl = "оно привело к неизвестной ошибке {error}"

    def __init__(
        self,
        operation: Operation,
        message: Message,
        error: Exception,
    ):
        super().__init__(operation=operation, message=message, error=error)


class MessageCleanedFullyError(MessageBaseError):
    """Сообщение при очистке осталось без текста."""

    end_tmpl = "при очистке оно осталось без текста и не будет опубликовано в категории"
