import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

from initialization import user
from log import logger
from models import Source, Category, Filter
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.helpers.senders import send_message_to_main_user
from plugins.bot.menu.managers.input_wait import input_wait_manager
from plugins.bot.menu.section_source import list_source


def list_category_buttons(
        path: Path, button_show_all_title='') -> list[list]:
    query = (Category
             .select(Category.id,
                     Category.title,
                     peewee.fn.Count(Source.id).alias('count'))
             .join(Source, peewee.JOIN.LEFT_OUTER)
             .group_by(Category.id))
    return buttons.get_list_model(
        data={f'{item.id}': (item.title, item.count) for item in query},
        path=path,
        prefix_path='c',
        button_show_all_title=button_show_all_title,
    )


def main_menu(data: Message | CallbackQuery) -> (str, list[list]):
    path = Path('/')

    text = '**Агрегатор каналов**'

    inline_keyboard = []
    if is_admin(data.from_user.id):
        inline_keyboard.append([InlineKeyboardButton(
            '➕',
            callback_data=path.add_action('add')
        ), InlineKeyboardButton(
            '⚙',
            callback_data='/o/'
        ), ])
    inline_keyboard += list_category_buttons(path, f'📚 Все источники')
    inline_keyboard.append([InlineKeyboardButton(
        f'🔘 Общие фильтры',
        callback_data=path.add_value('s', 0)
    )])

    return text, inline_keyboard


@Client.on_callback_query(filters.regex(
    r'^/$'))
async def set_main_menu(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    text, inline_keyboard = main_menu(callback_query)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_callback_query(filters.regex(
    r's_\d+/:edit/$') & custom_filters.admin_only)
async def choice_source_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_obj: Source = Source.get(id=int(path.get_value('s')))
    text = (f'Источник: {await source_obj.get_formatted_link()}\n\n'
            f'Ты **меняешь категорию** у источника.\n'
            f'Выбери новую категорию:')

    inline_keyboard = list_category_buttons(path) + buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(
    r'^/:add/$|^/c_\d+/:edit/$') & custom_filters.admin_only)
async def add_edit_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    text = 'ОК. Ты меняешь канал для категории, '
    if Path(callback_query.data).action == 'add':
        text = 'ОК. Ты добавляешь новую категорию с каналом, '
    text += ('в который будут пересылаться сообщения из источников. '
             'Этот бот должен быть администратором канала '
             'с возможностью публиковать записи.\n\n'
             '**Введи ID или ссылку на канал:**')

    await callback_query.answer()
    await callback_query.message.reply(text)

    input_wait_manager.add(
        callback_query.message.chat.id, add_edit_category_waiting_input,
        client, callback_query)


async def add_edit_category_waiting_input(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    input_text = re.sub('https://t.me/', '', message.text)
    path = Path(callback_query.data)

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Назад')),
            disable_web_page_preview=True)

    try:
        chat = await user.get_chat(input_text)
    except (exceptions.BadRequest, exceptions.NotAcceptable) as err:
        await reply(f'❌ Что-то пошло не так\n\n{err}')
        return

    if chat.type != ChatType.CHANNEL:
        await reply('❌ Это не канал')
        return

    try:
        member = await chat.get_member(client.me.id)
        if not member.privileges.can_post_messages:
            await reply('❌ Бот не имеет прав на публикацию в этом канале')
            return
    except exceptions.bad_request_400.UserNotParticipant:
        await reply('❌ Бот не администратор этого канала')
        return

    try:
        await user.join_chat(input_text)
    except Exception as err:
        await reply(f'❌ Основной клиент не может подписаться на канал\n\n'
                    f'{err}')
        return

    try:
        if path.action == 'add':
            category_obj: Category = Category.create(
                tg_id=chat.id, title=chat.title)
            success_text = (f'✅ Категория '
                            f'**{await category_obj.get_formatted_link()}** '
                            f'добавлена')
        else:
            category_id = int(path.get_value('c'))
            q = (Category
                 .update({Category.tg_id: chat.id,
                          Category.title: chat.title})
                 .where(Category.id == category_id))
            q.execute()
            success_text = (f'✅ Категория {category_id} '
                            f'изменена на **{chat.title}**')
        Category.clear_actual_cache()
    except peewee.IntegrityError:
        await reply('❗️Этот канал уже используется')
        return

    await reply(success_text)

    await send_message_to_main_user(client, callback_query, success_text)

    callback_query.data = path.get_prev()
    if path.action == 'add':
        await set_main_menu(client, callback_query)
        return
    await list_source(client, callback_query)


@Client.on_callback_query(filters.regex(
    r'c_\d+/:delete/') & custom_filters.admin_only)
async def delete_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    category_obj: Category = Category.get(id=int(path.get_value('c')))
    if path.with_confirmation:
        category_obj.delete_instance()
        Category.clear_actual_cache()
        Source.clear_actual_cache()
        Filter.clear_actual_cache()

        callback_query.data = '/'
        await callback_query.answer('Категория удалена')
        await set_main_menu(client, callback_query)

        await send_message_to_main_user(
            client, callback_query,
            f'Удалена категория **{await category_obj.get_formatted_link()}**')
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        f'Категория: **{await category_obj.get_formatted_link()}**\n\n'
        'Ты **удаляешь** категорию!',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            '❌ Подтвердить удаление',
            callback_data=f'{path}/'
        ), ]] + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )
