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
                entity_text = text[entity.offset:entity.offset+entity.length]
                if (entity_text
                        in Filter.global_hashtag()
                        + channel.get_blacklist_hashtag()):
                    logger.debug('Сообщение %s отфильтровано по hashtag',
                                 message.id)
                    return True

            if entity.type == MessageEntityType.TEXT_LINK:
                for part_url in (Filter.global_part_of_url()
                                 + channel.get_blacklist_part_of_url()):
                    if part_url in entity.url:
                        logger.debug(
                            'Сообщение %s отфильтровано по part_of_url',
                            message.id)
                        return True

            if entity.type in (MessageEntityType.CASHTAG,
                               MessageEntityType.EMAIL,
                               MessageEntityType.PHONE_NUMBER,
                               MessageEntityType.BANK_CARD):
                logger.debug('Сообщение %s отфильтровано по '
                             'CASHTAG|EMAIL|PHONE_NUMBER|BANK_CARD',
                             message.id)
                return True

    for part_text in (Filter.global_part_of_text()
                      + channel.get_blacklist_part_of_text()):
        if text and part_text.lower() in text.lower():
            logger.debug('Сообщение %s отфильтровано по part_of_text',
                         message.id)
            return True

    if Filter.global_reply_markup() + channel.get_blacklist_reply_markup():
        if message.reply_markup:
            logger.debug('Сообщение %s отфильтровано по reply_markup',
                         message.id)
            return True

    return False

promo_message = filters.create(is_promo_message)
