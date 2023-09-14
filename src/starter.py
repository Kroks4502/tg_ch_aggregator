import logging
from asyncio import sleep
from operator import attrgetter

from peewee import DoesNotExist
from pyrogram.errors import RPCError
from pyrogram.types import Dialog

from clients import bot, user
from models import Category, Source, User
from plugins.user.sources_monitoring.new_message import new_message


async def startup():
    while (
        not user.is_connected
        or not user.is_initialized
        or not bot.is_connected
        or not bot.is_initialized
    ):
        await sleep(0.1)

    msg = "Запущен начальный скрипт"
    logging.info(msg)
    me = await user.get_me()
    await bot.send_message(me.id, msg)

    try:
        user_obj = User.get(id=me.id)
        if not user_obj.is_admin:
            user_obj.is_admin = True
            user_obj.save()
    except DoesNotExist:
        User.create(id=me.id, username="UserBot", is_admin=True)

    await update_admin_usernames(me.id)

    new_messages = await get_unread_messages()
    for message in sorted(new_messages, key=attrgetter("date")):
        await new_message(user, message)

    logging.info(
        f"Начальный скрипт завершил работу. Обработано сообщений: {len(new_messages)}."
    )
    await bot.send_message(
        me.id,
        (
            "Начальный скрипт завершил работу.\n"
            f"Обработано сообщений: **{len(new_messages)}**."
        ),
    )


async def update_admin_usernames(user_bot_tg_id: int):
    db_data = {admin.id: admin.username for admin in User.select()}

    actual = {}
    for admin_id in db_data:
        if admin_id != user_bot_tg_id:
            try:
                admin = await user.get_users(admin_id)
                actual.update({admin.id: admin.username})
            except RPCError as e:
                logging.warning(e, exc_info=True)

    for tg_id, username in actual.items():
        if (
            username
            and username != db_data[tg_id]
            or not username
            and f"…{str(tg_id)[-5:]}" != db_data[tg_id]
        ):
            q = User.update(
                {User.username: username if username else f"…{str(tg_id)[-5:]}"}
            ).where(User.id == tg_id)
            q.execute()


async def get_unread_messages() -> list:
    db_channels = {item.id: [Category, item.title, False] for item in Category.select()}
    db_channels.update(
        {item.id: [Source, item.title, False] for item in Source.select()}
    )

    sources_ids = [source.id for source in Source.select(Source.id)]
    new_messages = []
    async for dialog in user.get_dialogs():
        update_source_title(dialog, db_channels)
        if dialog.unread_messages_count != 0 and dialog.chat.id in sources_ids:
            media_group_ids = set()  # {media_group_id ...}
            async for message in user.get_chat_history(
                dialog.chat.id, dialog.unread_messages_count
            ):
                if message.media_group_id:
                    if message.media_group_id not in media_group_ids:
                        media_group_ids.update({message.media_group_id})
                        new_messages.append(message)
                else:
                    new_messages.append(message)
    await check_sources_in_dialogs(db_channels)
    return new_messages


def update_source_title(dialog: Dialog, db_channels: dict):
    if dialog.chat.id in db_channels:
        db_channels[dialog.chat.id][2] = True
        if db_channels[dialog.chat.id][1] != dialog.chat.title:
            model = db_channels[dialog.chat.id][0]
            q = model.update({model.title: dialog.chat.title}).where(
                model.id == dialog.chat.id
            )
            q.execute()


async def check_sources_in_dialogs(db_channels: dict):
    for tg_id, data in db_channels.items():
        if data[2] is False:
            mgs = f"Источника {tg_id} {data[1]} нет в диалогах UserBot"
            logging.warning(mgs)
            for admin in User.select():
                try:
                    await bot.send_message(admin.id, mgs)
                except RPCError as e:
                    logging.error(e, exc_info=True)
