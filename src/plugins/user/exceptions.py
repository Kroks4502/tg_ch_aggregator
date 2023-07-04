class UserBaseError(Exception):
    ...


class MessageBaseError(UserBaseError):
    ...


class RepeatedMessageError(MessageBaseError):
    """Повторное сообщение."""


class FilteredMessageError(MessageBaseError):
    """Отфильтрованное сообщение."""


class MediaMessageWithoutCaptionError(MessageBaseError):
    """Сообщение не может содержать подпись."""
