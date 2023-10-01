from peewee import DoesNotExist
from pyrogram import Client

from models import MessageHistory
from plugins.bot import router
from plugins.bot.menu import Menu

MESSAGE_NOT_EXISTS = "Сообщение было удалено источником"

GET_CATEGORY_MESSAGE_BUTTON_TEXT = "Сообщение категории"
GET_CATEGORY_MESSAGE_PATH = "/c/{category_id}/m/{message_id}/"


@router.page(
    path=GET_CATEGORY_MESSAGE_PATH.format(category_id=r"-\d+", message_id=r"\d+")
)
async def get_category_message(
    client: Client,
    menu: Menu,
):
    category_id = menu.path.get_value("c")
    category_message_id = menu.path.get_value("m")

    try:
        history_obj: MessageHistory = MessageHistory.get(
            category_id=category_id,
            category_message_id=category_message_id,
        )
    except DoesNotExist:
        await client.send_message(
            chat_id=menu.user.id,
            text=MESSAGE_NOT_EXISTS,
        )
        return

    if history_obj.category_media_group_id:
        message_ids = _get_media_group_message_ids(
            category_id=category_id,
            category_media_group_id=history_obj.category_media_group_id,
        )
    else:
        message_ids = category_message_id

    await client.forward_messages(
        chat_id=menu.user.id,
        from_chat_id=category_id,
        message_ids=message_ids,
    )


def _get_media_group_message_ids(category_id: int, category_media_group_id: str):
    return (
        i.category_message_id
        for i in MessageHistory.select(MessageHistory.category_message_id).where(
            (MessageHistory.category_id == category_id)
            & (MessageHistory.category_media_group_id == category_media_group_id)
        )
    )
