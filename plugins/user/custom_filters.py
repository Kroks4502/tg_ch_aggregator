import re

from pyrogram import filters
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from initialization import MONITORED_CHANNELS_ID, logger
from models import Filter, Source


async def is_forward_from_chat(_, __, message):
    return message.forward_from_chat is not None


forward_from_chat = filters.create(is_forward_from_chat)


async def is_monitored_channels(_, __, message):
    return message.chat.id in MONITORED_CHANNELS_ID


monitored_channels = filters.create(is_monitored_channels)


async def is_promo_message(_, __, message: Message):
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    channel = Source.get(tg_id=message.chat.id)
    if entities:
        for entity in entities:
            if entity.type == MessageEntityType.HASHTAG:
                entity_text = text[entity.offset:entity.offset + entity.length]
                if (entity_text
                        in Filter.global_hashtag()
                        + channel.get_blacklist_hashtag()):
                    msg = f'Сообщение {message.id} отфильтровано по hashtag: {entity_text}'
                    logger.debug(msg)
                    return True, msg

            elif entity.type == MessageEntityType.TEXT_LINK:
                for part_url in (Filter.global_part_of_url()
                                 + channel.get_blacklist_part_of_url()):
                    if re.search(part_url, entity.url, flags=re.IGNORECASE):
                        msg = f'Сообщение {message.id} отфильтровано по part_of_url: {part_url}'
                        logger.debug(msg)
                        return True, msg

            elif entity.type in (MessageEntityType.CASHTAG,
                                 MessageEntityType.EMAIL,
                                 MessageEntityType.PHONE_NUMBER,
                                 MessageEntityType.BANK_CARD):
                msg = f'Сообщение {message.id} отфильтровано по CASHTAG|EMAIL|PHONE_NUMBER|BANK_CARD'
                logger.debug(msg)
                return True, msg

    if text:
        for part_text in (Filter.global_part_of_text()
                          + channel.get_blacklist_part_of_text()):
            if re.search(part_text, text, flags=re.IGNORECASE):
                msg = f'Сообщение {message.id} отфильтровано по part_of_text: {part_text}'
                logger.debug(msg)
                return True, msg

    if Filter.global_reply_markup() + channel.get_blacklist_reply_markup():
        if message.reply_markup:
            msg = f'Сообщение {message.id} отфильтровано по reply_markup'
            logger.debug(msg)
            return True, msg

    return False, ''


promo_message = filters.create(is_promo_message)
