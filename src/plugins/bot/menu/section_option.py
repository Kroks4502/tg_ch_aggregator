import datetime as dt
import math
import os
from operator import itemgetter

import peewee
from pyrogram import Client, filters
from pyrogram.enums import ChatType
from pyrogram.errors import RPCError
from pyrogram.types import (CallbackQuery, InlineKeyboardMarkup,
                            InlineKeyboardButton, Message)

from clients import user
from common import get_message_link, get_shortened_text
from filter_types import FILTER_TYPES_BY_ID
from log import logger
from models import (Admin, CategoryMessageHistory, Source,
                    FilterMessageHistory, Category, Filter)
from plugins.bot.menu import custom_filters
from plugins.bot.menu.utils import buttons
from plugins.bot.menu.utils.links import (get_user_formatted_link,
                                          get_channel_formatted_link)
from plugins.bot.menu.utils.managers import input_wait_manager
from plugins.bot.menu.utils.path import Path
from plugins.bot.menu.utils.senders import send_message_to_admins
from settings import LOGS_DIR, DB_FILEPATH


@Client.on_callback_query(filters.regex(
    r'^/o/$') & custom_filters.admin_only)
async def options(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer()
    await callback_query.message.edit_text(
        '**Параметры**',
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton(
                    'Администраторы',
                    callback_data='/o/a/'
                ), ],
                [InlineKeyboardButton(
                    'История фильтра',
                    callback_data='/o/fh/'
                ), ],
                [InlineKeyboardButton(
                    'История пересылки',
                    callback_data='/o/mh/'
                ), ],
                [InlineKeyboardButton(
                    'Статистика',
                    callback_data='/o/statistics/'
                ), ],
                [InlineKeyboardButton(
                    '💾 Логи',
                    callback_data='/o/:get_logs/'
                ), InlineKeyboardButton(
                    '💾 db',
                    callback_data='/o/:get_db/'
                ), ],
                [InlineKeyboardButton(
                    'Проверить пост',
                    callback_data='/o/:check_post/'
                ), ],
            ] + buttons.get_fixed(Path(callback_query.data))))


@Client.on_callback_query(filters.regex(
    r'^/o/statistics/$') & custom_filters.admin_only)
async def statistics(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)
    text = '**Статистика бота за время работы**\n\n'

    query = Category.select()
    text += f'Категории: {query.count()} шт.\n'

    query = Source.select()
    text += f'Источники: {query.count()} шт.\n'

    query = Filter.select()
    text += f'Фильтры: {query.count()} шт.\n\n'

    today = dt.datetime.today()
    month_ago = today - dt.timedelta(days=30)
    week_ago = today - dt.timedelta(days=7)
    day_ago = today - dt.timedelta(days=1)

    text += f'📰 **Переслано сообщений за последний период**\n'
    query = CategoryMessageHistory.select().where((CategoryMessageHistory.deleted == False)
                                                  & (CategoryMessageHistory.date > day_ago))
    text += f'— День: {query.count()} шт.\n'
    query = CategoryMessageHistory.select().where((CategoryMessageHistory.deleted == False)
                                                  & (CategoryMessageHistory.date > week_ago))
    text += f'— Неделя: {query.count()} шт.\n'
    query = CategoryMessageHistory.select().where((CategoryMessageHistory.deleted == False)
                                                  & (CategoryMessageHistory.date > month_ago))
    text += f'— Месяц: {query.count()} шт.\n\n'
    text += f'**По категориям**\n'
    for category in Category.select():
        query = CategoryMessageHistory.select().where((CategoryMessageHistory.deleted == False)
                                                      & (CategoryMessageHistory.category == category))
        text += f'— {await get_channel_formatted_link(category.tg_id)}: {query.count()} шт.\n'
    query = CategoryMessageHistory.select().where(CategoryMessageHistory.deleted == False)
    text += f'__Всего за всё время переслано {query.count()} шт.__\n\n'

    text += f'🗑 **Отфильтровано сообщений за последний период**\n'
    query = FilterMessageHistory.select().where(FilterMessageHistory.date > day_ago)
    text += f'— День: {query.count()} шт.\n'
    query = FilterMessageHistory.select().where(FilterMessageHistory.date > week_ago)
    text += f'— Неделя: {query.count()} шт.\n'
    query = FilterMessageHistory.select().where(FilterMessageHistory.date > month_ago)
    text += f'— Месяц: {query.count()} шт.\n\n'

    text += f'**По источникам за последний месяц**\n'
    lines = []
    for source in Source.select():
        query = FilterMessageHistory.select().where((FilterMessageHistory.source == source) & (FilterMessageHistory.date > month_ago))
        query_count = query.count()
        hm_query = CategoryMessageHistory.select().where((CategoryMessageHistory.deleted == False)
                                                         & (CategoryMessageHistory.source == source)
                                                         & (CategoryMessageHistory.date > month_ago))
        total_count = query_count + hm_query.count()
        if p := query_count / total_count * 100 if total_count else 0:
            lines.append((f'{get_shortened_text(source.title, 25)}: {query_count} шт. ({p:0.1f}%)\n', p))
    text += ''.join([f'{i}. {" " if i < 10 else ""}{line[0]}' for i, line in enumerate(sorted(lines, key=itemgetter(1), reverse=True), start=1)])

    query = FilterMessageHistory.select()
    query_count = query.count()
    hm_query = CategoryMessageHistory.select().where(CategoryMessageHistory.deleted == False)
    total_count = query_count + hm_query.count()
    p = query_count / total_count * 100 if total_count else 0
    text += (f'__Всего за всё время отфильтровано {query_count} шт. '
             f'({p:0.1f}%)__\n\n')

    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(buttons.get_fixed(Path('/o/mh/'))),
        disable_web_page_preview=True)


MAX_NUM_ENTRIES_MESSAGE = 5


@Client.on_callback_query(filters.regex(
    r'^/o/mh/$|^/o/mh/p_\d+/$') & custom_filters.admin_only)
async def message_history(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)
    page = int(p) if (p := Path(callback_query.data).get_value('p')) else 1
    query = CategoryMessageHistory.select().order_by(CategoryMessageHistory.id.desc())
    obj_counts = query.count()
    text = '**Список пересланных сообщений в обратном порядке**\n\n'
    for item in query.paginate(page, MAX_NUM_ENTRIES_MESSAGE):
        text += (f'{"🏞" if item.media_group else "🗞"}'
                 f'{">📝" if item.source_message_edited else ""}'
                 f'{">🗑" if item.source_message_deleted else ""}'
                 f' [{get_shortened_text(item.source.title, 30)}]'
                 f'({get_message_link(item.source.tg_id, item.source_message_id)})\n'
                 f'✅{">🖨" if item.rewritten else ""}'
                 f'{">🗑" if item.deleted else ""}'
                 f' [{get_shortened_text(item.category.title, 30)}]'
                 f'({get_message_link(item.category.tg_id, item.message_id)})\n'
                 f'__{item.source_message_id} {item.date.strftime("%Y.%m.%d, %H:%M:%S")}__'
                 f'\n\n')
    text += f'Всего записей: **{obj_counts}**'
    inline_keyboard = [[]]
    if page > 1:
        inline_keyboard[0].append(InlineKeyboardButton(
            'Предыдущие',
            callback_data=f'/o/mh/p_{page - 1}/'))
    if page < math.ceil(obj_counts / MAX_NUM_ENTRIES_MESSAGE):
        inline_keyboard[0].append(InlineKeyboardButton(
            'Следующие',
            callback_data=f'/o/mh/p_{page + 1}/'))
    inline_keyboard += buttons.get_fixed(Path('/o/mh/'))
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_callback_query(filters.regex(
    r'^/o/fh/$|^/o/fh/p_\d+/$') & custom_filters.admin_only)
async def filter_history(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)
    page = int(p) if (p := Path(callback_query.data).get_value('p')) else 1
    query = FilterMessageHistory.select().order_by(FilterMessageHistory.id.desc())
    obj_counts = query.count()
    text = '**Список отфильтрованных сообщений в обратном порядке**\n\n'
    for item in query.paginate(page, MAX_NUM_ENTRIES_MESSAGE):
        text += (f'{"🏞" if item.media_group else "🗞"}'
                 f'[{get_shortened_text(item.source.title, 30)}]'
                 f'({get_message_link(item.source.tg_id, item.source_message_id)})\n'
                 f'**{"Персональный" if item.filter.source else "Общий"}** фильтр '
                 f'**{FILTER_TYPES_BY_ID.get(item.filter.type)}**\n'
                 f'`{item.filter.pattern}`\n'
                 f'__{item.source_message_id} {item.date.strftime("%Y.%m.%d, %H:%M:%S")}__'
                 f'\n\n')
    text += f'Всего записей: **{obj_counts}**'
    inline_keyboard = [[]]
    if page > 1:
        inline_keyboard[0].append(InlineKeyboardButton(
            'Предыдущие',
            callback_data=f'/o/fh/p_{page - 1}/'))
    if page < math.ceil(obj_counts / MAX_NUM_ENTRIES_MESSAGE):
        inline_keyboard[0].append(InlineKeyboardButton(
            'Следующие',
            callback_data=f'/o/fh/p_{page + 1}/'))
    inline_keyboard += buttons.get_fixed(Path('/o/fh/'))
    await callback_query.answer()
    await callback_query.message.edit_text(
        text, reply_markup=InlineKeyboardMarkup(inline_keyboard))


@Client.on_callback_query(filters.regex(
    r'^/o/:get_logs/$') & custom_filters.admin_only)
async def get_logs(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer('Загрузка...')
    info_message = ''
    for filename in os.listdir(LOGS_DIR):
        file_path = LOGS_DIR / filename
        if os.stat(file_path).st_size:
            await callback_query.message.reply_document(file_path)
        else:
            info_message += f'Файл **{filename}** пуст\n'
    if info_message:
        await callback_query.message.reply(info_message)


@Client.on_callback_query(filters.regex(
    r'^/o/:get_db/') & custom_filters.admin_only)
async def get_db(_, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer('Загрузка...')
    await callback_query.message.reply_document(DB_FILEPATH)


@Client.on_callback_query(filters.regex(
    r'^/o/a/$') & custom_filters.admin_only)
async def list_admins(_, callback_query: CallbackQuery, *, needs_an_answer: bool = True):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)

    text = f'**Список администраторов:**'

    inline_keyboard = [[InlineKeyboardButton(
        '✖ Добавить',
        callback_data=path.add_action('add')
    ), ]]

    query = (Admin
             .select(Admin.id,
                     Admin.username, ))
    inline_keyboard += buttons.get_list_model(
        data={f'{item.id}': (item.username, 0) for item in query},
        path=path,
        prefix_path='u',
    )
    inline_keyboard += buttons.get_fixed(path)
    if needs_an_answer:
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
    text = f'**{await get_user_formatted_link(admin_obj.tg_id)}**\n\n'

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

    async def reply(text):
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons.get_fixed(path, back_title='Назад')),
            disable_web_page_preview=True)

    try:
        chat = await client.get_chat(message.text)
    except RPCError as e:
        await reply(f'❌ Что-то пошло не так\n\n{e}')
        return

    if chat.type != ChatType.PRIVATE:
        await reply('❌ Это не пользователь')
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
        await reply(f'❗️Этот пользователь уже администратор')
        return

    success_text = (f'✅ Администратор '
                    f'**{await get_user_formatted_link(admin_obj.tg_id)}** добавлен')
    await reply(success_text)

    callback_query.data = path.get_prev()
    await list_admins(client, callback_query, needs_an_answer=False)

    await send_message_to_admins(client, callback_query, success_text)
    return


@Client.on_callback_query(filters.regex(
    r'u_\d+/:delete/') & custom_filters.admin_only)
async def delete_admin(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    path = Path(callback_query.data)
    admin_id = int(path.get_value('u'))
    admin_obj: Admin = Admin.get(id=admin_id)
    text = f'**{await get_user_formatted_link(admin_obj.tg_id)}**'
    if path.with_confirmation:
        q = (Admin
             .delete()
             .where(Admin.id == admin_id))
        q.execute()

        Admin.clear_actual_cache()

        callback_query.data = path.get_prev(3)
        await callback_query.answer('Администратор удален')
        await list_admins(client, callback_query, needs_an_answer=False)

        await send_message_to_admins(
            client, callback_query, f'❌ Удален администратор {text}')
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


@Client.on_callback_query(filters.regex(
    r'^/o/:check_post/$') & custom_filters.admin_only)
async def check_post(client: Client, callback_query: CallbackQuery):
    logger.debug(callback_query.data)

    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты хочешь проверить есть ли пост в истории.\n\n'
        '**Перешли пост в этот чат и я проверю.**')
    input_wait_manager.add(
        callback_query.message.chat.id, check_post_waiting_forwarding, client)


async def check_post_waiting_forwarding(
        _, message: Message):
    async def reply(text, b=None):
        if not b:
            b = []
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                b + buttons.get_fixed(
                    Path('/o/'), back_title='Назад')),
            disable_web_page_preview=True)

    if not message.forward_from_chat:
        await reply('🫥 Это не пересланный пост')
        return

    chat_id = message.forward_from_chat.id
    message_id = message.forward_from_message_id
    source = Source.get_or_none(tg_id=chat_id)
    m_history_obj = None
    f_history_obj = None
    if source:
        m_history_obj = CategoryMessageHistory.get_or_none(
            source=source,
            source_message_id=message_id, )
        f_history_obj = FilterMessageHistory.get_or_none(
            source=source,
            source_message_id=message_id, )

    if not m_history_obj:
        m_history_obj = CategoryMessageHistory.get_or_none(
            forward_from_chat_id=chat_id,
            forward_from_message_id=message_id, )

    if f_history_obj:
        await reply(f'⚠️ [Пост]'
                    f'({get_message_link(f_history_obj.source.tg_id, f_history_obj.source_message_id)}) '
                    f'был отфильтрован',
                    [[InlineKeyboardButton(
                        'Перейти к фильтру',
                        callback_data=f'/f_{f_history_obj.filter.id}/'
                    ), ], ])
        return

    if not m_history_obj:
        await reply(f'❌ [Поста]'
                    f'({get_message_link(message.forward_from_chat.id, message.forward_from_message_id)})'
                    f' нет в истории')
        return

    await reply(f'✅ [Пост]'
                f'({get_message_link(m_history_obj.source.tg_id, m_history_obj.source_message_id)}) '
                f'был опубликован в канале [{m_history_obj.category.title}]'
                f'({get_message_link(m_history_obj.category.tg_id, m_history_obj.message_id)})')
