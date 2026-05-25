from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)
from peewee import SQL

from clients import dispatcher
from common.menu_paths import CATEGORY_DETAIL_PATH, SOURCE_DETAIL_PATH
from models import Category, Source
from plugins.bot.middlewares.admin import _is_admin_cached

MAX_INLINE_ITEMS = 10


@dispatcher.inline_query()
async def search_channel(inline_query: InlineQuery):
    if not await _is_admin_cached(inline_query.from_user.id):
        await inline_query.answer([], cache_time=1)
        return

    offset = int(inline_query.offset) if inline_query.offset else 0

    source_query = Source.select(Source.id, Source.title, SQL("'source'").alias("type"))
    category_query = Category.select(
        Category.id, Category.title, SQL("'category'").alias("type")
    )

    scq = source_query | category_query

    query = (
        Source.select(scq.c.id, scq.c.title, scq.c.type)
        .from_(scq)
        .order_by(SQL("title"))
        .offset(offset)
        .limit(MAX_INLINE_ITEMS)
    )

    if inline_query.query:
        query = query.where(scq.c.title.contains(inline_query.query))

    await inline_query.answer(
        [
            InlineQueryResultArticle(
                id=str(item.id),
                title=item.title,
                input_message_content=InputTextMessageContent(message_text=item.title),
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            (
                                InlineKeyboardButton(
                                    text="Открыть",
                                    callback_data=CATEGORY_DETAIL_PATH.format(
                                        category_id=item.id
                                    )
                                    + "?new",
                                )
                                if item.type == "category"
                                else InlineKeyboardButton(
                                    text="Открыть",
                                    callback_data=SOURCE_DETAIL_PATH.format(
                                        source_id=item.id
                                    )
                                    + "?new",
                                )
                            )
                        ]
                    ]
                ),
            )
            for item in query
        ],
        cache_time=1,
        next_offset=str(offset + MAX_INLINE_ITEMS),
    )
