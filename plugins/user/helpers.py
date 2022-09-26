from pyrogram.types import Message

from models import History


def save_history(message: Message | list[int, int, str], status: str):
    if isinstance(message, list):
        from_chat = message[0]
        message_id = message[1]
        media_group_id = (message[2]
                          if message[2] else '')
    else:
        from_chat = message.chat.id
        message_id = message.id
        media_group_id = (message.media_group_id
                          if message.media_group_id else '')

    History.create(from_chat=from_chat,
                   message_id=message_id,
                   media_group_id=media_group_id,
                   status=status,)
