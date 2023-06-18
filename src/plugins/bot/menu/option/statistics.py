import datetime as dt

from _operator import itemgetter
from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from common import get_shortened_text
from models import Category, Filter, MessageHistory, Source
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/stat/$') & custom_filters.admin_only,
)
async def statistics(_, callback_query: CallbackQuery):
    await callback_query.answer('Загрузка...')

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

    text += '📰 **Переслано сообщений за последний период**\n'

    query = MessageHistory.select().where(
        (MessageHistory.category_message_id != None)  # noqa
        & (MessageHistory.created_at > day_ago)
    )
    text += f'— День: {query.count()} шт.\n'

    query = MessageHistory.select().where(
        (MessageHistory.category_message_id != None)  # noqa
        & (MessageHistory.created_at > week_ago)
    )
    text += f'— Неделя: {query.count()} шт.\n'

    query = MessageHistory.select().where(
        (MessageHistory.category_message_id != None)  # noqa
        & (MessageHistory.created_at > month_ago)
    )
    text += f'— Месяц: {query.count()} шт.\n\n'

    text += '**По категориям**\n'
    for category in Category.select():
        query = MessageHistory.select().where(
            (MessageHistory.category_message_id != None)  # noqa
            & (MessageHistory.category == category)
        )
        text += (
            f'— {await get_channel_formatted_link(category.id)}:'
            f' {query.count()} шт.\n'
        )
    query = MessageHistory.select().where(
        MessageHistory.category_message_id != None  # noqa
    )
    text += f'__Всего за всё время переслано {query.count()} шт.__\n\n'

    text += '🗑 **Отфильтровано сообщений за последний период**\n'

    query = MessageHistory.select().where(
        (MessageHistory.filter_id != None)  # noqa
        & (MessageHistory.created_at > day_ago)
    )
    text += f'— День: {query.count()} шт.\n'

    query = MessageHistory.select().where(
        (MessageHistory.filter_id != None)  # noqa
        & (MessageHistory.created_at > week_ago)
    )
    text += f'— Неделя: {query.count()} шт.\n'

    query = MessageHistory.select().where(
        (MessageHistory.filter_id != None)  # noqa
        & (MessageHistory.created_at > month_ago)
    )
    text += f'— Месяц: {query.count()} шт.\n\n'

    text += '**По источникам за последний месяц**\n'
    lines = []
    for source in Source.select():
        query = MessageHistory.select().where(
            (MessageHistory.source == source)
            & (MessageHistory.filter_id != None)  # noqa
            & (MessageHistory.created_at > month_ago)
        )
        query_count = query.count()

        query = MessageHistory.select().where(
            (MessageHistory.source == source) & (MessageHistory.created_at > month_ago)
        )
        total_count = query.count()
        if p := query_count / total_count * 100 if total_count else 0:
            lines.append(
                (
                    (
                        f'{get_shortened_text(source.title, 25)}: {query_count} шт.'
                        f' ({p:0.1f}%)\n'
                    ),
                    p,
                )
            )
    text += ''.join(
        [
            f'{i}. {" " if i < 10 else ""}{line[0]}'
            for i, line in enumerate(
                sorted(lines, key=itemgetter(1), reverse=True), start=1
            )
        ]
    )

    query = MessageHistory.select().where(MessageHistory.filter_id != None)  # noqa
    query_count = query.count()

    query = MessageHistory.select()
    total_count = query_count + query.count()
    p = query_count / total_count * 100 if total_count else 0
    text += f'__Всего за всё время отфильтровано {query_count} шт. ({p:0.1f}%)__\n\n'

    await callback_query.message.edit_text(
        text,
        reply_markup=Menu('/o/stat/').reply_markup,
        disable_web_page_preview=True,
    )
