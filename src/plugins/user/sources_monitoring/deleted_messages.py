import logging

from pyrogram import Client
from pyrogram.types import Message

from common import get_shortened_text
from models import CategoryMessageHistory, Source
from plugins.user.utils import custom_filters


@Client.on_deleted_messages(
    custom_filters.monitored_channels,
)
async def deleted_messages(client: Client, messages: list[Message]):
    logging.debug(
        'Получено обновление об удалении сообщений источников '
        f'{[(message.chat.title, message.chat.id, message.id) for message in messages]}'
    )

    for message in messages:
        history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
            source=Source.get_or_none(tg_id=message.chat.id),
            source_message_id=message.id,
            deleted=False,
        )
        if history_obj:
            amount_deleted = await client.delete_messages(
                history_obj.category.tg_id, history_obj.message_id
            )
            history_obj.source_message_deleted = True
            history_obj.deleted = True
            history_obj.save()
            if amount_deleted:
                logging.info(
                    f'Сообщение {history_obj.source_message_id} из источника '
                    f'{get_shortened_text(history_obj.source.title, 20)} {history_obj.source.tg_id} было удалено. '
                    f'Оно удалено из категории {get_shortened_text(history_obj.category.title, 20)} '
                    f'{history_obj.category.tg_id}'
                )
            else:
                logging.info(
                    f'Сообщение {history_obj.source_message_id} из источника '
                    f'{get_shortened_text(history_obj.source.title, 20)} {history_obj.source.tg_id} было удалено. '
                    f'Оно УЖЕ удалено из категории {get_shortened_text(history_obj.category.title, 20)} '
                    f'{history_obj.category.tg_id}'
                )
