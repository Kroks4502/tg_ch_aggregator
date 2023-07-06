import datetime as dt
import json
import logging

from pyrogram import Client
from pyrogram import errors as pyrogram_errors
from pyrogram import filters
from pyrogram.types import Message

from models import MessageHistory
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageNotFoundOnHistoryError,
    MessageNotOnCategoryError,
    Operation,
)
from plugins.user.utils import custom_filters

DELETE = Operation.DELETE


@Client.on_deleted_messages(
    custom_filters.monitored_channels & ~filters.service,
)
async def deleted_messages(client: Client, messages: list[Message]):
    for message in messages:
        logging.debug(
            'Источник %s удалил сообщение %s',
            message.chat.id,
            message.id,
        )

        history_obj: MessageHistory = MessageHistory.get_or_none(
            source_id=message.chat.id,
            source_message_id=message.id,
        )
        history_obj.deleted_at = dt.datetime.now()  # todo check timezone !
        history_obj.data.append(dict(deleted=json.loads(message.__str__())))

        exc = None
        try:
            if not history_obj:
                raise MessageNotFoundOnHistoryError(operation=DELETE, message=message)

            if not history_obj.category_message_id:
                raise MessageNotOnCategoryError(operation=DELETE, message=message)

            await client.delete_messages(
                history_obj.category.tg_id, history_obj.message_id
            )

            history_obj.category_message_id = None

            logging.info(
                'Источник %s удалил сообщение %s, оно удалено из категории',
                message.chat.id,
                message.id,
            )
        except MessageBaseError as e:
            exc = e
        except pyrogram_errors.BadRequest as error:
            exc = MessageBadRequestError(operation=DELETE, message=message, error=error)
        finally:
            if exc and history_obj:
                history_obj.data[-1]['exception'] = dict(
                    operation=DELETE.name,
                    text=exc.text,
                )

            history_obj.save()
