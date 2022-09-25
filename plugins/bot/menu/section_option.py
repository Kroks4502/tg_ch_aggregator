import os

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)

from initialization import user
from log import logger
from models import Admin
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.helpers.senders import send_message_to_main_user
from plugins.bot.menu.managers.input_wait import input_wait_manager
from settings import LOGS_DIR, BASE_DIR


@Client.on_callback_query(filters.regex(
    r'^/o/$') & custom_filters.admin_only)
async def options(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    text = '**Параметры**'

    inline_keyboard = [
        [InlineKeyboardButton(
            'Администраторы',
            callback_data='/o/a/'
        ), ],
        [InlineKeyboardButton(
            '💾 Логи',
            callback_data='/o/:get_logs'
        ), InlineKeyboardButton(
            '💾 db',
            callback_data='/o/:get_db'
        ), ]
    ]

    inline_keyboard += buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_callback_query(filters.regex(
    r'^/o/:get_logs$') & custom_filters.admin_only)
async def get_logs(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer('Загрузка...')
    info_message = ''
    for filename in os.listdir(LOGS_DIR):
        file_path = os.path.join(LOGS_DIR, filename)
        if os.stat(file_path).st_size:
            await callback_query.message.reply_document(file_path)
        else:
            info_message += f'Файл **{filename}** пуст\n'
    if info_message:
        await callback_query.message.reply(info_message)


@Client.on_callback_query(filters.regex(
    r'^/o/:get_db') & custom_filters.admin_only)
async def get_db(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer('Загрузка...')
    await callback_query.message.reply_document(os.path.join(BASE_DIR, '.db'))


@Client.on_callback_query(filters.regex(
    r'^/o/a/$') & custom_filters.admin_only)
async def list_admins(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    text = f'**Список администраторов:**'

    inline_keyboard = [[InlineKeyboardButton(
        '✖ Добавить',
        callback_data=path.add_action('add')
    ), ]]

    query = (Admin
             .select(Admin.id,
                     Admin.username,))
    inline_keyboard += buttons.get_list_model(
        data={f'{item.id}': (item.username, 0) for item in query},
        path=path,
        prefix_path='u',
    )
    inline_keyboard += buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_callback_query(filters.regex(
    r'^/o/a/u_\d+/$') & custom_filters.admin_only)
async def detail_admin(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    admin_id = int(path.get_value('u'))
    admin_obj: Admin = Admin.get(id=admin_id)
    text = f'**{await admin_obj.get_formatted_link()}**\n\n'

    inline_keyboard = []
    if admin_obj.tg_id != user.me.id:
        inline_keyboard.append([InlineKeyboardButton(
            '✖️ Удалить',
            callback_data=path.add_action('delete')
        ), ])
    inline_keyboard += buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(
    r'^/o/a/:add/$') & custom_filters.admin_only)
async def add_admin(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    chat_id = callback_query.message.chat.id

    text = ('ОК. Ты добавляешь нового администратора.\n\n'
            '**Введи ID или имя пользователя:**')

    await callback_query.answer()
    await callback_query.message.reply(text)
    input_wait_manager.add(
        chat_id, add_admin_waiting_input, client, callback_query)


async def add_admin_waiting_input(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    reply_markup_fix_buttons = InlineKeyboardMarkup(
        buttons.get_fixed(path, back_title='Назад'))

    try:
        chat = await client.get_chat(message.text)
    except (exceptions.BadRequest, exceptions.NotAcceptable) as err:
        await message.reply_text(
            f'❌ Что-то пошло не так\n\n{err}',
            reply_markup=reply_markup_fix_buttons)
        return

    if chat.type != ChatType.PRIVATE:
        await message.reply_text(
            '❌ Это не пользователь',
            reply_markup=reply_markup_fix_buttons)
        return

    try:
        if chat.username:
            username = chat.username
        else:
            username = (f'{chat.first_name + " " if chat.first_name else ""}'
                        f'{chat.last_name + " " if chat.last_name else ""}')
        admin_obj = Admin.create(tg_id=chat.id, username=username)
        Admin.clear_actual_cache()
    except peewee.IntegrityError:
        await message.reply_text(
            f'❗️Этот пользователь уже администратор',
            reply_markup=reply_markup_fix_buttons)
        return

    text = f'✅ Администратор **{await admin_obj.get_formatted_link()}** ' \
           f'добавлен'
    await message.reply_text(
        text,
        reply_markup=reply_markup_fix_buttons, disable_web_page_preview=True)

    callback_query.data = path.get_prev()

    await list_admins(client, callback_query)

    await send_message_to_main_user(client, callback_query, text)
    return


@Client.on_callback_query(filters.regex(
    r'u_\d+/:delete/') & custom_filters.admin_only)
async def delete_admin(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    admin_id = int(path.get_value('u'))
    admin_obj: Admin = Admin.get(id=admin_id)
    text = f'**{await admin_obj.get_formatted_link()}**'
    if path.with_confirmation:
        q = (Admin
             .delete()
             .where(Admin.id == admin_id))
        q.execute()

        Admin.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Администратор удален')
        await list_admins(client, callback_query)

        await send_message_to_main_user(
            client, callback_query, f'Удален администратор {text}')
        return

    text += '\n\nТы **удаляешь** администратора!'

    inline_keyboard = [[InlineKeyboardButton(
        '❌ Подтвердить удаление',
        callback_data=f'{path}/'
    ), ]]
    inline_keyboard += buttons.get_fixed(path)

    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True
    )
