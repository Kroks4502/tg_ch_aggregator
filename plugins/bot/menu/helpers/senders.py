from pyrogram import Client
from pyrogram.types import CallbackQuery

from initialization import user


async def send_message_to_main_user(
        client: Client, callback_query: CallbackQuery, text):
    f_user = callback_query.from_user
    if f_user.id != user.me.id:
        if f_user.username:
            b_text = f'@{f_user.username}'
        else:
            full_name = (
                f'{f_user.first_name + " " if f_user.first_name else ""}'
                f'{f_user.last_name + " " if f_user.last_name else ""}')
            b_text = f'({f_user.id})' if full_name else f'{f_user.id}'
        await client.send_message(
            user.me.id, f'{b_text} {text}', disable_web_page_preview=True)
