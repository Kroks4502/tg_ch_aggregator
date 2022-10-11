from asyncio import sleep
from operator import itemgetter

from log import logger
from initialization import user, bot
from models import Admin, Category, Source


async def startup():
    while not user.is_connected or not bot.is_connected:
        await sleep(0.1)

    msg = 'Запущен начальный #скрипт'
    logger.info(msg)
    me = await user.get_me()
    await bot.send_message(me.id, msg)

    if not Admin.select().where(Admin.tg_id == me.id).exists():
        Admin.create(tg_id=me.id, username=me.username if me.username else me.id)

    msg = 'Начальный #скрипт завершил работу'
    logger.info(msg)
    await bot.send_message(me.id, msg)


# async def update_admin_usernames():
#     db_data = {admin.tg_id: admin.username for admin in Admin.select()}
#     actual = {admin.id: admin.username
#               for admin in await user.get_users(list(db_data.keys()))}
#     for tg_id in actual:
#         if actual[tg_id] != db_data[tg_id]:
#             q = (Admin
#                  .update({Admin.username: actual[tg_id]})
#                  .where(Admin.tg_id == tg_id))
#             q.execute()


def update_channel_titles(dialog, db_channel_titles):
    if dialog.chat.id in db_channel_titles:
        if db_channel_titles[dialog.chat.id][1] != dialog.chat.title:
            model = db_channel_titles[dialog.chat.id][0]
            q = (model
                 .update({model.title: dialog.chat.title})
                 .where(model.tg_id == dialog.chat.id))
            q.execute()
