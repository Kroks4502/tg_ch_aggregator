import logging

from pyrogram.errors import ChannelPrivate
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from clients import bot_client, user_client
from common.senders import send_message_to_admins
from models import Category, Source
from plugins.bot.handlers.category.detail import CATEGORY_CALLBACK_DATA
from plugins.bot.handlers.source.detail import DETAIL_SOURCE_PATH
from settings import USER_BOT_NAME

GO_TO_CATEGORY = "Перейти к категории"
GO_TO_SOURCE = "Перейти к источнику"

ERROR_NOT_FOUND_CHANNEL = (
    f"{{channel_title}} ({{channel_id}}) отсутствует в диалогах {USER_BOT_NAME}"
)
ERROR_NOT_FOUND_CATEGORY = f"Категория {ERROR_NOT_FOUND_CHANNEL}"
ERROR_NOT_FOUND_SOURCE = f"Источник {ERROR_NOT_FOUND_CHANNEL}"


async def update_channels_info_job():
    user_client_chats = {
        dialog.chat.id: dialog.chat async for dialog in user_client.get_dialogs()
    }

    for db_obj in (
        *Source.select().where(Source.is_deleted == False),
        *Category.select(),
    ):
        tg_chat = user_client_chats.get(db_obj.id)

        if not tg_chat:
            try:
                tg_chat = await user_client.get_chat(db_obj.id)
            except ChannelPrivate as e:
                logging.warning("Не удалось получить информацию о канале %s: %s", db_obj.id, e)
                tg_chat = None

        if not tg_chat:
            await send_not_found_chat_message_to_admins(db_obj)
            continue

        if tg_chat.title != db_obj.title:
            db_obj.title = tg_chat.title
            db_obj.save()


async def send_not_found_chat_message_to_admins(db_obj: Source | Category):
    if isinstance(db_obj, Source):
        text = ERROR_NOT_FOUND_SOURCE.format(
            channel_title=db_obj.title,
            channel_id=db_obj.id,
        )
        button_text = GO_TO_SOURCE
        callback_data = DETAIL_SOURCE_PATH.format(source_id=db_obj.id) + "?new"
    else:
        text = ERROR_NOT_FOUND_CATEGORY.format(
            channel_title=db_obj.title,
            channel_id=db_obj.id,
        )
        button_text = GO_TO_CATEGORY
        callback_data = CATEGORY_CALLBACK_DATA.format(category_id=db_obj.id) + "?new"

    logging.warning(text)
    await send_message_to_admins(
        client=bot_client,
        text=text,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=callback_data,
                    )
                ],
            ]
        ),
    )
