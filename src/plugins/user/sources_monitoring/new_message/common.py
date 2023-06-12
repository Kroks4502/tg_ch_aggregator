import logging
from functools import wraps

from pyrogram import Client
from pyrogram.errors import (
    BadRequest,
    ChatForwardsRestricted,
    MediaCaptionTooLong,
    MessageIdInvalid,
    MessageTooLong,
)
from pyrogram.types import Message


def logging_on_startup(message: Message, is_resending: bool):
    logging.debug(
        'Источник %s отправил сообщение %s, is_resending %s',
        message.chat.id,
        message.id,
        is_resending,
    )


def handle_errors_on_new_message(f):
    """Декоратор для отлова возможных исключений при отправке новых сообщений в категорию."""

    @wraps(f)
    async def decorated(client: Client, message: Message, *args, **kwargs):
        try:
            return await f(client, message, *args, **kwargs)
        except MessageIdInvalid as error:
            # Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника
            logging.warning(
                'Источник %s отправил сообщение %s, оно привело к ошибке %s',
                message.chat.id,
                message.id,
                error,
            )
        except ChatForwardsRestricted:
            # todo: Перепечатывать сообщение
            logging.error(
                'Источник %s отправил сообщение %s, но запрещает пересылку сообщений',
                message.chat.id,
                message.id,
            )
        except (MediaCaptionTooLong, MessageTooLong):
            # todo Обрезать и ставить надпись "Читать из источника..."
            logging.error(
                'Источник %s отправил сообщение %s, но при перепечатывании оно превышает лимит знаков',
                message.chat.id,
                message.id,
            )
        except BadRequest as error:
            logging.error(
                'Источник %s отправил сообщение %s, оно привело к непредвиденной ошибке %s. Полное сообщение: %s',
                message.chat.id,
                message.id,
                error,
                message,
                exc_info=True,
            )

    return decorated
