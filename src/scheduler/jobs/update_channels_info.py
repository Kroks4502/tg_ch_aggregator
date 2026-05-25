import logging

from pyrogram.errors import ChannelPrivate

from clients import user_client
from common.dto import AdminNotification, Button, ButtonRow
from common.menu_paths import CATEGORY_DETAIL_PATH, SOURCE_DETAIL_PATH
from common.notifier_registry import get_admin_notifier
from models import Category, Source
from settings import USER_BOT_NAME

logger = logging.getLogger(__name__)

GO_TO_CATEGORY = "Перейти к категории"
GO_TO_SOURCE = "Перейти к источнику"

ERROR_NOT_FOUND_CHANNEL = (
    f"{{channel_title}} ({{channel_id}}) отсутствует в диалогах {USER_BOT_NAME}"
)
ERROR_NOT_FOUND_CATEGORY = f"Категория {ERROR_NOT_FOUND_CHANNEL}"
ERROR_NOT_FOUND_SOURCE = f"Источник {ERROR_NOT_FOUND_CHANNEL}"


async def update_channels_info_job():
    logger.debug("Starting job...")
    user_client_chats = {
        dialog.chat.id: dialog.chat async for dialog in user_client.get_dialogs()
    }

    for db_obj in (
        *Source.select().where(Source.is_deleted == False),
        *Category.select(),
    ):
        logger.debug(f"Updating info about {db_obj.id}...")
        tg_chat = user_client_chats.get(db_obj.id)

        if not tg_chat:
            try:
                tg_chat = await user_client.get_chat(db_obj.id)
            except ChannelPrivate as e:
                logging.warning(
                    "Не удалось получить информацию о канале %s: %s",
                    db_obj.id,
                    e,
                )
                tg_chat = None

        if not tg_chat:
            await send_not_found_chat_message_to_admins(db_obj)
            continue

        if tg_chat.title != db_obj.title:
            db_obj.title = tg_chat.title
            db_obj.save()
            logger.info(f"Title for {db_obj.id} updated")
    logger.debug("Job completed")


async def send_not_found_chat_message_to_admins(db_obj: Source | Category):
    logger.debug(f"Sending message to admins about not found chat {db_obj.id}...")
    if isinstance(db_obj, Source):
        text = ERROR_NOT_FOUND_SOURCE.format(
            channel_title=db_obj.title,
            channel_id=db_obj.id,
        )
        button_text = GO_TO_SOURCE
        callback_data = SOURCE_DETAIL_PATH.format(source_id=db_obj.id) + "?new"
    else:
        text = ERROR_NOT_FOUND_CATEGORY.format(
            channel_title=db_obj.title,
            channel_id=db_obj.id,
        )
        button_text = GO_TO_CATEGORY
        callback_data = CATEGORY_DETAIL_PATH.format(category_id=db_obj.id) + "?new"

    logger.warning(text)
    await get_admin_notifier().notify(
        AdminNotification(
            text=text,
            button_rows=(
                ButtonRow(
                    buttons=(Button(text=button_text, callback_data=callback_data),)
                ),
            ),
        )
    )
    logger.info(f"Message to admins about not found chat {db_obj.id} sent")
