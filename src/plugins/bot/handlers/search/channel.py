from peewee import SQL
from pyrogram import Client
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from models import Category, Source
from plugins.bot.handlers.category.detail import CATEGORY_CALLBACK_DATA
from plugins.bot.handlers.source.detail import DETAIL_SOURCE_PATH
from utils.custom_filters import admin_only

MAX_INLINE_ITEMS = 10


@Client.on_inline_query(admin_only)
async def search_channel(_, inline_query: InlineQuery):
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
                title=item.title,
                input_message_content=InputTextMessageContent(item.title),
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            (
                                InlineKeyboardButton(
                                    "Открыть",
                                    callback_data=CATEGORY_CALLBACK_DATA.format(
                                        category_id=item.id
                                    )
                                    + "?new",
                                )
                                if item.type == "category"
                                else InlineKeyboardButton(
                                    "Открыть",
                                    callback_data=DETAIL_SOURCE_PATH.format(
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
