import logging
from string import Formatter

import telethon
from telethon.tl.patched import Message

from plugins.user.types import Operation
from plugins.user.utils.chats_locks import MessagesLocks
from settings import APP_START_DATETIME


class UserBaseError(Exception):
    pass


class MessageBaseError(UserBaseError):
    logging_stack_info = False
    logging_exc_info = None
    logging_level = logging.INFO

    message_tmpl = "{chat_id} {operation} {event_id}"
    additional_message_tmpl = None

    def __init__(
        self,
        chat_id: int,
        event_id: int,
        operation: Operation,
        **kwargs,
    ):
        self.chat_id = chat_id
        self.event_id = event_id
        self.operation = operation
        self.kwargs = kwargs
        self.text = self.generate_message()
        logging.log(
            level=self.logging_level,
            msg=f"{self.__class__.__name__} : {self.text}",
            exc_info=self.logging_exc_info,
            stack_info=self.logging_stack_info,
        )

    def generate_message(self):
        text_items = [
            self.message_tmpl.format(
                chat_id=self.chat_id,
                operation=self.operation.value,
                event_id=self.event_id,
            )
        ]

        if self.additional_message_tmpl:
            text_items.append(
                self.additional_message_tmpl.format(
                    **{
                        key: self.kwargs.pop(key, "<undefined>")
                        for _, key, _, _ in Formatter().parse(
                            self.additional_message_tmpl
                        )
                        if key
                    }
                )
            )

        if self.kwargs:
            text_items.append(
                ", ".join((f"{key}={value}" for key, value in self.kwargs.items()))
            )

        return f"{', '.join(text_items)}."

    def to_dict(self):
        return dict(
            name=self.__class__.__name__,
            level=logging.getLevelName(self.logging_level),
            text=self.text,
            operation=self.operation.name,
        )

    def __str__(self):
        return f"{self.__class__.__name__} : {self.text}"


class MessageBlockedByIdError(MessageBaseError):
    """Сообщение было ранее заблокировано по message.id."""

    additional_message_tmpl = "оно заблокировано {blocked}"


class MessageNotFoundOnHistoryError(MessageBaseError):
    """Сообщения нет в истории."""

    logging_level = logging.WARNING
    additional_message_tmpl = "его нет в истории date={date}, edit_date={edit_date}"

    def __init__(
        self,
        chat_id: int,
        event_id: int,
        operation: Operation,
        message: Message,
    ):
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

        kwargs = dict(
            chat_id=chat_id,
            event_id=event_id,
            operation=operation,
            date=message.date,
            edit_date=message.edit_date,
        )

        if not message.date and operation != Operation.DELETE:
            kwargs["message"] = message

        super().__init__(**kwargs)


class MessageNotOnCategoryError(MessageBaseError):
    """Сообщение не публиковалось в категории."""

    additional_message_tmpl = "оно не публиковалось в категории"


class MessageNotRewrittenError(MessageBaseError):
    """Сообщение нельзя отредактировать."""

    additional_message_tmpl = (
        "оно не может быть изменено в категории, "
        "потому что было переслано и не перепечатывалось"
    )


class MessageNotModifiedError(MessageBaseError):
    """Сообщение не удалось перепечатать."""

    additional_message_tmpl = "перепечатать сообщение в категории не удалось {error}"

    def __init__(
        self,
        chat_id: int,
        event_id: int,
        operation: Operation,
        message: Message,
        error: telethon.errors.MessageNotModifiedError,
    ):
        super().__init__(
            chat_id=chat_id,
            event_id=event_id,
            operation=operation,
            message=message,
            error=error,
        )


class MessageRepeatedError(MessageBaseError):
    """Сообщение уже опубликовано в категории."""

    additional_message_tmpl = "оно уже опубликовано в категории"


class MessageFilteredError(MessageBaseError):
    """Сообщение не прошло фильтрацию."""

    additional_message_tmpl = "оно было отфильтровано"


class MessageMediaWithoutCaptionError(MessageBaseError):
    """Сообщение не может содержать подпись."""

    additional_message_tmpl = "но оно не может содержать подпись"


class MessageIdInvalidError(MessageBaseError):
    """Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника."""

    logging_level = logging.WARNING
    additional_message_tmpl = "оно привело к ошибке {error}"


class MessageForwardsRestrictedError(MessageBaseError):
    """Сообщение запрещено пересылать."""

    logging_level = logging.WARNING
    additional_message_tmpl = "но запрещает пересылку сообщений"


class MessageTooLongError(MessageBaseError):
    """Сообщение содержит слишком длинный текст."""

    logging_level = logging.ERROR
    additional_message_tmpl = "при перепечатывании оно превышает лимит знаков {error}"


class MessageBadRequestError(MessageBaseError):
    """Сообщение привело к необработанной ошибке при запросе."""

    logging_level = logging.ERROR
    additional_message_tmpl = "оно привело к необработанной ошибке при запросе {error}"


class MessageUnknownError(MessageBaseError):
    """Сообщение привело к неизвестной ошибке."""

    logging_level = logging.ERROR
    additional_message_tmpl = "оно привело к неизвестной ошибке {error}"


class MessageCleanedFullyError(MessageBaseError):
    """Сообщение при очистке осталось без текста."""

    additional_message_tmpl = (
        "при очистке оно осталось без текста и не будет опубликовано в категории"
    )
