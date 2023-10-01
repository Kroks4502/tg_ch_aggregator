from peewee import DoesNotExist
from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup

from alerts.regex_rule import FIRING_COUNTER_BUTTON_GET_MSG_TEXT
from models import MessageHistory
from plugins.bot import router
from plugins.bot.menu import Menu

MESSAGE_NOT_EXISTS = "Сообщение было удалено источником"


@router.page(path=r"/c/-\d+/m/\d+/", admin_only=False)
async def get_category_message(
    client: Client,
    menu: Menu,
    callback_query: CallbackQuery,
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
        await _remove_message_button(callback_query)
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
    await _remove_message_button(callback_query)


def _get_media_group_message_ids(category_id: int, category_media_group_id: str):
    return (
        i.category_message_id
        for i in MessageHistory.select(MessageHistory.category_message_id).where(
            (MessageHistory.category_id == category_id)
            & (MessageHistory.category_media_group_id == category_media_group_id)
        )
    )


async def _remove_message_button(callback_query: CallbackQuery):
    inline_keyboard = []
    for line in callback_query.message.reply_markup.inline_keyboard:
        inline_keyboard.append([])
        for button in line:
            if getattr(button, "text", "") != FIRING_COUNTER_BUTTON_GET_MSG_TEXT:
                inline_keyboard[-1].append(button)

    await callback_query.message.edit_reply_markup(
        InlineKeyboardMarkup(inline_keyboard)
    )
