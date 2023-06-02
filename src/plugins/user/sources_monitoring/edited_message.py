import logging

from pyrogram import Client
from pyrogram.types import Message

from common import get_shortened_text
from config import MESSAGES_EDIT_LIMIT_TD
from models import CategoryMessageHistory, Source
from plugins.user.sources_monitoring.blocking import (
    blocking_editable_messages,
    blocking_received_media_groups,
)
from plugins.user.sources_monitoring.message_with_media_group import (
    message_with_media_group,
)
from plugins.user.sources_monitoring.message_without_media_group import (
    message_without_media_group,
)
from plugins.user.utils import custom_filters


@Client.on_edited_message(
    custom_filters.monitored_channels,
)
async def edited_message(client: Client, message: Message):
    logging.debug(
        f'Источник {get_shortened_text(message.chat.title, 20)} {message.chat.id} '
        f'изменил сообщение {message.id}'
    )

    if message.edit_date - message.date > MESSAGES_EDIT_LIMIT_TD:
        logging.info(
            f'Сообщение {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} изменено'
            f' спустя {(message.edit_date - message.date).seconds // 60} мин.'
        )
        return

    blocked = blocking_editable_messages.get(message.chat.id)
    if blocked.contains(message.media_group_id) or blocked.contains(message.id):
        logging.warning(
            f'Изменение сообщения {message.id} '
            'из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} заблокировано.'
        )
        return
    blocked.add(message.media_group_id if message.media_group_id else message.id)

    history_obj: CategoryMessageHistory = CategoryMessageHistory.get_or_none(
        source=Source.get_or_none(tg_id=message.chat.id),
        source_message_id=message.id,
        deleted=False,
    )
    if not history_obj:
        logging.warning(
            f'Измененного сообщения {message.id} из источника'
            f' {get_shortened_text(message.chat.title, 20)} {message.chat.id} от'
            f' {message.date} нет в истории.'
        )
        blocked.remove(message.media_group_id if message.media_group_id else message.id)
        return

    if history_obj.media_group:
        messages_to_delete = []
        query = CategoryMessageHistory.select().where(
            (CategoryMessageHistory.source == history_obj.source)
            & (CategoryMessageHistory.media_group == history_obj.media_group)
            & (CategoryMessageHistory.deleted == False)
        )
        for m in query:
            messages_to_delete.append(m.message_id)
    else:
        messages_to_delete = [history_obj.message_id]

    if messages_to_delete:
        await client.delete_messages(history_obj.category.tg_id, messages_to_delete)

        if history_obj.media_group:
            query = CategoryMessageHistory.select().where(
                (CategoryMessageHistory.category == history_obj.category)
                & (CategoryMessageHistory.message_id << messages_to_delete)
            )
        else:
            query = [history_obj]

        for h in query:
            h.source_message_edited = True
            h.deleted = True
            h.save()
            logging.info(
                f'Сообщение {h.source_message_id} из источника'
                f' {get_shortened_text(h.source.title, 20)} {h.source.tg_id} было'
                ' изменено. Оно удалено из категории'
                f' {get_shortened_text(h.category.title, 20)} {h.category.tg_id}'
            )

        if message.media_group_id:
            if b := blocking_received_media_groups.get(message.chat.id):
                b.remove(message.media_group_id)
            await message_with_media_group(client, message, is_resending=True)
        else:
            await message_without_media_group(client, message, is_resending=True)

    blocked.remove(message.media_group_id if message.media_group_id else message.id)
