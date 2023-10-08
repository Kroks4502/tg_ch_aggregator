from datetime import datetime, timedelta

from pyrogram.types import Message

from alerts.configs import AlertCounterHistory
from common.links import get_message_link
from common.text import get_words
from models import AlertHistory, MessageHistory, Source
from plugins.bot.constants.settings import FORMAT_TIMESTAMP
from plugins.bot.handlers.alert_rules.common.constants import (
    ALERT_COUNTER_MAX_MESSAGES,
    ALERT_COUNTER_MAX_WORDS,
    ALERT_RULE_DETAIL_PATH,
    SINGULAR_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.category.message import GET_CATEGORY_MESSAGE_PATH
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text
from plugins.bot.utils.links import get_channel_formatted_link

FIRING_REGEX_ALERT_RULE_CATEGORY = "В категории {category_link}"
FIRING_REGEX_ALERT_RULE_TITLE = (
    "За последние {interval} мин. опубликовано сообщений: {amount} шт."
)


async def get_alert_counter_messages(
    menu: Menu,
    alert_obj: AlertHistory,
    firing_right_now: bool,
):
    alert_data = AlertCounterHistory(**alert_obj.data)

    end_ts = alert_obj.fired_at

    query_messages = _get_query_history_category_messages(
        category_id=alert_obj.category_id,
        start_ts=end_ts - timedelta(minutes=alert_data.count_interval),
        end_ts=end_ts,
    )

    pagination = menu.set_pagination(
        total_items=query_messages.count(), size=ALERT_COUNTER_MAX_MESSAGES
    )
    category_messages = query_messages.paginate(
        pagination.page, pagination.size
    ).execute()

    menu.add_row_many_buttons(
        *(
            (
                f"#{n}",
                GET_CATEGORY_MESSAGE_PATH.format(
                    category_id=mh.category_id,
                    message_id=mh.category_message_id,
                ),
            )
            for n, mh in enumerate(category_messages, 1)
        )
    )

    title = FIRING_REGEX_ALERT_RULE_TITLE.format(
        interval=alert_data.count_interval,
        amount=alert_data.actual_amount_messages,
    )
    if alert_obj.category_id:
        category_link = await get_channel_formatted_link(alert_obj.category_id)
        title = (
            FIRING_REGEX_ALERT_RULE_CATEGORY.format(
                category_link=category_link,
            )
            + f" {title.lower()}"
        )

    if firing_right_now:
        menu.add_row_button_after_pagination(
            text=SINGULAR_ALERT_RULE_TITLE,
            path=ALERT_RULE_DETAIL_PATH.format(rule_id=alert_obj.alert_rule_id),
            new=True,
        )
        menu.set_footer_buttons = False
    else:
        title = f"__{alert_obj.fired_at.strftime(FORMAT_TIMESTAMP)}__\n\n" + title

    category_messages_text = _get_category_messages_texts(category_messages)
    return get_menu_text(
        title=title,
        content="\n\n".join(category_messages_text),
    )


def _get_query_history_category_messages(
    category_id: int,
    start_ts: datetime,
    end_ts: datetime,
):
    mh: MessageHistory = MessageHistory.alias()
    where = (
        (mh.created_at > start_ts)
        & (mh.created_at < end_ts)
        & (mh.category_message_id.is_null(False))
        & (mh.repeat_history_id.is_null())
        & (mh.deleted_at.is_null())
        & (
            mh.data.path("last_message_without_error").is_null(False)
            & (
                mh.data.path("last_message_without_error", "category", "text").is_null(
                    False
                )
                | mh.data.path(
                    "last_message_without_error", "category", "caption"
                ).is_null(False)
            )
            | mh.data.path("last_message_without_error").is_null()
            & (
                mh.data.path("first_message", "category", "text").is_null(False)
                | mh.data.path("first_message", "category", "caption").is_null(False)
            )
        )
    )
    if category_id:
        where = (mh.category_id == category_id) & where

    return (
        mh.select(
            mh.category_id,
            mh.category_message_id,
            mh.category_message_rewritten,
            mh.data,
            Source.title_alias,
            Source.title,
        )
        .where(where)
        .join(Source)
    )


def _get_category_messages_texts(query) -> list[str]:
    lines = []
    for n, row in enumerate(query, 1):
        line_num = 2 if row.category_message_rewritten else 0
        if short_text := get_short_text(row.data, line=line_num):
            url = get_message_link(
                chat_id=row.category_id,
                message_id=row.category_message_id,
            )
            link = f"**[>>>]({url})**"
            lines.append(
                f"`#{n}` **{row.source.title_alias or row.source.title}**:"
                f" {short_text} {link}"
            )

    return lines


def get_short_text(data: dict, line: int) -> str:
    if not data or not (
        message_data := (
            (data.get("last_message_without_error") or data.get("first_message")).get(
                "category"
            )
        )
    ):
        return ""

    if "_" not in message_data:
        return ""

    message_data.pop("_")
    message = Message(**message_data)
    text = message.text or message.caption
    if text:
        words = get_words(text=text, line=line)

        return " ".join(words[:ALERT_COUNTER_MAX_WORDS]).rstrip(".,:;?!\"'`)(") + (
            "…" if len(words) > ALERT_COUNTER_MAX_WORDS else ""
        )

    return ""
