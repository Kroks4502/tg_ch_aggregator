from peewee import fn
from pyrogram.types import Message

from alerts.common import get_alert_rule_title
from common.links import get_message_link
from common.text import get_words
from models import AlertRule, MessageHistory, Source
from plugins.bot import router
from plugins.bot.handlers.alert_rules.common.constants import (
    SINGULAR_ALERT_RULE_TEXT,
    SINGULAR_ALERT_RULE_TITLE,
)
from plugins.bot.handlers.category.message import GET_CATEGORY_MESSAGE_PATH
from plugins.bot.menu import Menu
from plugins.bot.menu_text import get_menu_text

TITLE = f"Сработало {SINGULAR_ALERT_RULE_TEXT} {{}}"
MAX_WORDS = 20
MAX_CATEGORY_MESSAGES = 8

ALERT_COUNTER_MESSAGES_PATH = "/r/{rule_id}/m/start/{start_ts}/end/{end_ts}/"


@router.page(
    path=ALERT_COUNTER_MESSAGES_PATH.format(
        rule_id=r"\d+",
        start_ts=r"\d+",
        end_ts=r"\d+",
    ),
    pagination=True,
)
async def get_alert_counter_messages(menu: Menu):
    rule_id = menu.path.get_value("r")
    start_ts = menu.path.get_value("start")
    end_ts = menu.path.get_value("end")

    rule_obj = AlertRule.get(rule_id)
    query_messages = _get_query_history_category_messages(
        category_id=rule_obj.category_id,
        start=start_ts,
        end=end_ts,
    )

    pagination = menu.set_pagination(
        total_items=query_messages.count(), size=MAX_CATEGORY_MESSAGES
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
    menu.add_row_button_after_pagination(
        SINGULAR_ALERT_RULE_TITLE, f"/r/{rule_obj.id}/", new=True
    )
    menu.set_footer_buttons = False

    category_messages_text = _get_category_messages_texts(category_messages)
    return get_menu_text(
        title=TITLE.format(get_alert_rule_title(rule_obj)),
        content="\n\n".join(category_messages_text),
    )


def _get_query_history_category_messages(category_id: int, start: int, end: int):
    mh: MessageHistory = MessageHistory.alias()
    where = (
        (mh.created_at > fn.TO_TIMESTAMP(start))
        & (mh.created_at < fn.TO_TIMESTAMP(end))
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

    try:
        message_data.pop("_")
    except KeyError:
        return ""

    message = Message(**message_data)
    text = message.text or message.caption
    if text:
        words = get_words(text=text, line=line)

        return " ".join(words[:MAX_WORDS]).rstrip(".,:;?!\"'`)(") + (
            "…" if len(words) > MAX_WORDS else ""
        )

    return ""
