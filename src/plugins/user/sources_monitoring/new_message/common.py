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

from common import get_shortened_text


def handle_errors_on_new_message(f):
    """Декоратор для отлова возможных исключений при отправке новых сообщений в категорию."""

    @wraps(f)
    async def decorated(client: Client, message: Message, *args, **kwargs):
        try:
            return await f(client, message, *args, **kwargs)
        except MessageIdInvalid as e:
            # Случай когда почти одновременно приходит сообщение о редактировании и удалении сообщения из источника
            logging.warning(
                f'Сообщение {message.id} из источника'
                f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} привело к'
                f' ошибке {e}'
            )
        except ChatForwardsRestricted:
            # todo: Перепечатывать сообщение
            logging.error(
                f'Источник запрещает пересылку сообщений '
                f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
                'превысило лимит знаков при его перепечатывании.'
            )
        except (MediaCaptionTooLong, MessageTooLong):
            # todo Обрезать и ставить надпись "Читать из источника..."
            logging.error(
                f'Описание медиа сообщения {message.id} из источника '
                f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} '
                'превысило лимит знаков при его перепечатывании.'
            )
        except BadRequest as e:
            logging.error(
                (
                    f'Сообщение {message.id} из источника '
                    f'{get_shortened_text(message.chat.title, 20)} {message.chat.id} привело '
                    f'к непредвиденной ошибке\n{e}\nПолное сообщение: {message}\n'
                ),
                exc_info=True,
            )

    return decorated
