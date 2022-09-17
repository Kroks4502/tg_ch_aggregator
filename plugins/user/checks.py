import re

from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from initialization import logger
from models import Source, Filter


async def is_passed_filter(message: Message):
    text = message.text or message.caption
    entities = message.entities or message.caption_entities
    channel = Source.get(tg_id=message.chat.id)
    if entities:
        for entity in entities:
            if entity.type == MessageEntityType.HASHTAG:
                entity_text = text[entity.offset:entity.offset + entity.length]
                for hashtag in (Filter.global_hashtag()
                                + channel.get_blacklist_hashtag()):
                    if re.search(hashtag, entity_text, flags=re.IGNORECASE):
                        comment = f'hashtag: `{hashtag}`'
                        logger.debug(comment)
                        return False, comment

            elif entity.type == MessageEntityType.TEXT_LINK:
                for part_url in (Filter.global_part_of_url()
                                 + channel.get_blacklist_part_of_url()):
                    if re.search(part_url, entity.url, flags=re.IGNORECASE):
                        comment = f'part_of_url: `{part_url}`'
                        logger.debug(comment)
                        return False, comment

            elif entity.type == MessageEntityType.URL:
                for part_url in (Filter.global_part_of_url()
                                 + channel.get_blacklist_part_of_url()):
                    if re.search(
                            part_url,
                            text[entity.offset:entity.offset+entity.length],
                            flags=re.IGNORECASE):
                        comment = f'part_of_url: `{part_url}`'
                        logger.debug(comment)
                        return False, comment

            elif entity.type in (MessageEntityType.CASHTAG,
                                 MessageEntityType.EMAIL,
                                 MessageEntityType.PHONE_NUMBER,
                                 MessageEntityType.BANK_CARD):
                comment = f'CASHTAG|EMAIL|PHONE_NUMBER|BANK_CARD'
                logger.debug(comment)
                return False, comment

    if text:
        for part_text in (Filter.global_part_of_text()
                          + channel.get_blacklist_part_of_text()):
            if re.search(part_text, text, flags=re.IGNORECASE):
                comment = f'part_of_text: `{part_text}`'
                logger.debug(comment)
                return False, comment

    if Filter.global_reply_markup() + channel.get_blacklist_reply_markup():
        if message.reply_markup:
            comment = f'reply_markup'
            logger.debug(comment)
            return False, comment

    return True, ''
