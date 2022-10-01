from asyncio import sleep
from operator import itemgetter

from log import logger
from plugins.user.helpers import save_history
from settings import AGGREGATOR_CHANNEL, DEVELOP_MODE
from initialization import user, bot
from models import Admin, Category, Source


async def startup():
    while not user.is_connected or not bot.is_connected:
        await sleep(0.1)

    msg = 'Запущен начальный #скрипт'
    logger.debug(msg)
    me = await user.get_me()
    if not DEVELOP_MODE:
        await bot.send_message(me.id, msg)

    await update_admin_usernames()

    if not Admin.select().where(Admin.tg_id == me.id).exists():
        Admin.create(tg_id=me.id, username=me.username)

    def get_db_titles(model):
        return {item.tg_id: (model, item.title) for item in model.select()}

    db_channel_titles = get_db_titles(Category)
    db_channel_titles.update(get_db_titles(Source))

    dialogs = user.get_dialogs()
    new_messages = []
    async for dialog in dialogs:
        update_channel_titles(dialog, db_channel_titles)

        if (
                dialog.unread_messages_count != 0
                and dialog.chat.id in Source.get_cache_all_field('tg_id')
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

    msg = 'Начальный #скрипт завершил работу'
    if new_messages:
        for message in sorted(new_messages, key=itemgetter(2)):
            chat_id = message[0]
            msg_ids = message[1]
            try:
                new_message = await user.forward_messages(
                    AGGREGATOR_CHANNEL,
                    chat_id, msg_ids
                )
                await user.read_chat_history(chat_id, max(msg_ids))
                await new_message[0].reply(f'/sent_from {chat_id}')
                for msg_ig in msg_ids:
                    save_history([chat_id, msg_ig, '?'], 'OK')
            except Exception:
                for msg_ig in msg_ids:
                    save_history([chat_id, msg_ig, '?'], 'start_script failed')
                # Сервисные сообщения не пересылаются
                ...
        msg += f'. Обработано сообщений: {len(new_messages)}'

    logger.debug(msg)

    if not DEVELOP_MODE:
        await bot.send_message(user.me.id, msg)


async def update_admin_usernames():
    db_data = {admin.tg_id: admin.username for admin in Admin.select()}
    actual = {admin.id: admin.username
              for admin in await user.get_users(list(db_data.keys()))}
    for tg_id in actual:
        if actual[tg_id] != db_data[tg_id]:
            q = (Admin
                 .update({Admin.username: actual[tg_id]})
                 .where(Admin.tg_id == tg_id))
            q.execute()


def update_channel_titles(dialog, db_channel_titles):
    if dialog.chat.id in db_channel_titles:
        if db_channel_titles[dialog.chat.id][1] != dialog.chat.title:
            model = db_channel_titles[dialog.chat.id][0]
            q = (model
                 .update({model.title: dialog.chat.title})
                 .where(model.tg_id == dialog.chat.id))
            q.execute()
