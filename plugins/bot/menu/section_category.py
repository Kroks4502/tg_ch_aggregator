import re

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import exceptions, RPCError
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message, Chat,
                            ChatPrivileges)

from initialization import user
from log import logger
from models import Source, Category, Filter
from plugins.bot.menu import custom_filters
from plugins.bot.menu.helpers import buttons
from plugins.bot.menu.helpers.checks import is_admin
from plugins.bot.menu.helpers.links import get_channel_formatted_link
from plugins.bot.menu.helpers.path import Path
from plugins.bot.menu.helpers.senders import send_message_to_admins
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
async def choice_source_category(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    source_obj: Source = Source.get(id=int(path.get_value('s')))
    text = (f'Источник: {await get_channel_formatted_link(source_obj.tg_id)}'
            f'\n\nТы **меняешь категорию** у источника.\n'
            f'Выбери новую категорию:')

    inline_keyboard = list_category_buttons(path) + buttons.get_fixed(path)
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard),
        disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(
    r'^/:add/$') & custom_filters.admin_only)
async def add_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты добавляешь новую категорию, '
        'в которую будут пересылаться сообщения из источников. '
        'Будет создан новый канал-агрегатор.\n\n'
        '**Введи название новой категории:**')

    input_wait_manager.add(
        callback_query.message.chat.id, add_category_waiting_input,
        client, callback_query)


async def add_category_waiting_input(
        client: Client, message: Message, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    new_channel_name = f'{message.text} | Aggregator'
    new_message = await message.reply_text(
        f'⏳ Создаю канал «{new_channel_name}»…')

    async def reply(text):
        await new_message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(Path(callback_query.data),
                                  back_title='Назад')),
            disable_web_page_preview=True)

    if len(message.text) > 80:
        await reply(
            f'❌ Название категории не должно превышать 80 символов')
        return

    new_channel: Chat = await user.create_channel(
        new_channel_name, f'Создан ботом {client.me.username}')

    await new_channel.promote_member(
        client.me.id, ChatPrivileges(
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_promote_members=True,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_invite_users=True, ))

    category_obj: Category = Category.create(
        tg_id=new_channel.id, title=new_channel.title)
    success_text = (f'✅ Категория '
                    f'**{await get_channel_formatted_link(category_obj.tg_id)}'
                    f'** создана')

    await reply(success_text)


@Client.on_callback_query(filters.regex(
    r'^/c_\d+/:edit/$') & custom_filters.admin_only)
async def edit_category(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты меняешь канал для категории, '
        'в который будут пересылаться сообщения из источников. '
        'Этот бот должен быть администратором канала '
        'с возможностью публиковать записи.\n\n'
        '**Введи публичное имя канала или ссылку на канал:**')

    input_wait_manager.add(
        callback_query.message.chat.id, edit_category_waiting_input,
        client, callback_query)


async def edit_category_waiting_input(
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
    except RPCError as e:
        await reply(f'❌ Что-то пошло не так\n\n{e}')
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
        await user.join_chat(chat.username if chat.username else chat.id)
    except RPCError as e:
        await reply(f'❌ Основной клиент не может подписаться на канал\n\n'
                    f'{e}')
        return

    try:
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

    await send_message_to_admins(client, callback_query, success_text)

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

        await send_message_to_admins(
            client, callback_query,
            f'❌ Удалена категория '
            f'**{await get_channel_formatted_link(category_obj.tg_id)}**')
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        f'Категория: '
        f'**{await get_channel_formatted_link(category_obj.tg_id)}**\n\n'
        'Ты **удаляешь** категорию!',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            '❌ Подтвердить удаление',
            callback_data=f'{path}/'
        ), ]] + buttons.get_fixed(path)),
        disable_web_page_preview=True
    )
