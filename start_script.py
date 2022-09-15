import traceback
from operator import itemgetter

from initialization import (logger, user, MONITORED_CHANNELS_ID, BOT_CHAT_ID,
                            bot)


async def startup():
    msg = 'Запущен начальный #скрипт'
    logger.debug(msg)
    await bot.send_message(user.me.id, msg)

    dialogs = user.get_dialogs()
    new_messages = []
    async for dialog in dialogs:
        if (
                dialog.unread_messages_count != 0
                and dialog.chat.id in MONITORED_CHANNELS_ID
        ):
            dialog_messages = user.get_chat_history(
                dialog.chat.id, dialog.unread_messages_count)

            next_message = None
            messages_group = []
            while True:
                try:
                    if next_message:
                        messages_group = [next_message]
                    else:
                        messages_group = [await anext(dialog_messages)]
                    next_message = await anext(dialog_messages)
                    while (
                            messages_group[0].media_group_id
                            and next_message.media_group_id
                            and messages_group[0].media_group_id
                            == next_message.media_group_id
                    ):
                        messages_group.append(next_message)
                        next_message = await anext(dialog_messages)

                    # Добавляем новые сообщения
                    message_ids = [item.id for item in messages_group]
                    new_messages.append(
                        [
                            messages_group[0].chat.id,
                            message_ids,
                            messages_group[0].date
                        ]
                    )
                    messages_group = None
                except StopAsyncIteration:
                    message_ids = [item.id for item in messages_group]
                    new_messages.append(
                        [
                            messages_group[0].chat.id,
                            message_ids,
                            messages_group[0].date
                        ]
                    )
                    break
    if new_messages:
        for message in sorted(new_messages, key=itemgetter(2)):
            try:
                chat_id = message[0]
                msg_ids = message[1]
                new_message = await user.forward_messages(
                    BOT_CHAT_ID,
                    chat_id, msg_ids
                )
                await new_message[0].reply(f'/sent_from {chat_id}')
                await user.read_chat_history(chat_id, max(msg_ids))
            except Exception as err:
                logger.error(f'Произошла необработанная ошибка.\n'
                             f'message:\n{message}\n'
                             f'Traceback:\n{traceback.format_exc()}', )

    msg = 'Начальный #скрипт завершил работу'
    logger.debug(msg)
    await bot.send_message(user.me.id, msg)
