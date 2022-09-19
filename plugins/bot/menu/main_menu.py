from pyrogram import Client, filters
from pyrogram.types import Message

from plugins.bot.menu.section_category import list_category


@Client.on_message(filters.command('go'))
async def send_main_menu(client: Client, message: Message):
    new_menu = await client.send_message(
        message.chat.id,
        'Загрузка...'
    )
    callback_query = type('CQ', (), dict(
        message=new_menu, data='/', from_user=message.from_user
    ))
    await list_category(client, callback_query)
