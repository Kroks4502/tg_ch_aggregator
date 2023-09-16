import json
import logging

from pyrogram import Client
from pyrogram import errors as pyrogram_errors
from pyrogram import filters
from pyrogram.types import Message

from models import MessageHistory, Source
from plugins.user.exceptions import (
    MessageBadRequestError,
    MessageBaseError,
    MessageFilteredError,
    MessageIdInvalidError,
    MessageNotFoundOnHistoryError,
    MessageNotModifiedError,
    MessageNotOnCategoryError,
    MessageNotRewrittenError,
    MessageTooLongError,
    Operation,
)
from plugins.user.sources_monitoring.common import (
    add_header,
    cut_long_message,
    get_filter_id_or_none,
    get_input_media,
    set_blocking,
)
from plugins.user.utils import custom_filters
from plugins.user.utils.cleanup import cleanup_message
from pyrogram_fork.edit_media_message import EditMessageMedia

EDIT = Operation.EDIT


@Client.on_edited_message(
    custom_filters.monitored_channels & ~filters.service,
)
async def edit_regular_message(client: Client, message: Message):  # noqa: C901
    logging.debug(
        "Источник %s изменил сообщение %s",
        message.chat.id,
        message.id,
    )

    blocked = None
    history_obj = None
    history_data = {}
    exc = None
    try:
        blocked = set_blocking(
            operation=EDIT,
            message=message,
            block_value=message.id,
        )

        history_obj = MessageHistory.get_or_none(
            source_id=message.chat.id,
            source_message_id=message.id,
        )

        if not history_obj:
            raise MessageNotFoundOnHistoryError(operation=EDIT, message=message)

        history_obj.edited_at = message.edit_date
        history_data["source"] = json.loads(message.__str__())

        if not history_obj.category_message_id:
            raise MessageNotOnCategoryError(operation=EDIT, message=message)

        if not history_obj.category_message_rewritten:
            raise MessageNotRewrittenError(operation=EDIT, message=message)

        source = Source.get(message.chat.id)

        filter_id = get_filter_id_or_none(message=message, source_id=source.id)
        history_obj.filter_id = filter_id
        if filter_id:
            raise MessageFilteredError(operation=EDIT, message=message)

        # Первый await !
        is_media = not message.text

        if message.text or message.caption:
            cleanup_message(message=message, source=source, is_media=is_media)
            add_header(source=source, message=message)
            cut_long_message(message=message)

        if is_media:
            category_message = await EditMessageMedia.edit_message_media(
                client,
                chat_id=history_obj.category_id,
                message_id=history_obj.category_message_id,
                media=get_input_media(message=message),
            )
        else:
            category_message = await client.edit_message_text(
                chat_id=history_obj.category_id,
                message_id=history_obj.category_message_id,
                text=message.text,
                parse_mode=None,
                entities=message.entities,
                disable_web_page_preview=True,
            )

        logging.info(
            "Источник %s изменил сообщение %s, оно изменено в категории %s",
            message.chat.id,
            message.id,
            source.category_id,
        )

        history_data["category"] = json.loads(category_message.__str__())

    except MessageBaseError as e:
        exc = e
    except pyrogram_errors.MessageNotModified as error:
        exc = MessageNotModifiedError(operation=EDIT, message=message, error=error)
    except pyrogram_errors.MessageIdInvalid as error:
        exc = MessageIdInvalidError(operation=EDIT, message=message, error=error)
    except (
        pyrogram_errors.MediaCaptionTooLong,
        pyrogram_errors.MessageTooLong,
    ) as error:
        exc = MessageTooLongError(operation=EDIT, message=message, error=error)
    except pyrogram_errors.BadRequest as error:
        exc = MessageBadRequestError(operation=EDIT, message=message, error=error)
    finally:
        if blocked:
            blocked.remove(value=message.id)

        if history_obj:
            if exc:
                history_data["exception"] = exc.to_dict()
                history_obj.data["last_message_with_error"] = history_data
            else:
                history_obj.data["last_message_without_error"] = history_data

            history_obj.save()
