from pyrogram import Client, filters
from pyrogram.types import (InlineKeyboardMarkup, InlineKeyboardButton,
                            Message, CallbackQuery)


def main_menu():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            'Категории',
            callback_data='/c/'
        ),
        InlineKeyboardButton(
            'Источники',
            callback_data='/s/'
        ),
        InlineKeyboardButton(
            'Фильтры',
            callback_data='/f/'
        )
    ]])


@Client.on_message(filters.command('go'))
async def send_main_menu(client: Client, message: Message):
    await client.send_message(
        message.chat.id,
        '/',
        reply_markup=main_menu()
    )


@Client.on_callback_query(filters.regex(r'^/$'))
async def add_main_menu(_, callback_query: CallbackQuery):
    await callback_query.message.edit_text(
        callback_query.data,
        reply_markup=main_menu()
    )
