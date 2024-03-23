import enum

from telethon.tl import types


@enum.unique
class FilterType(enum.Enum):
    HASHTAG = 1
    URL = 2
    TEXT = 3
    ENTITY_TYPE = 4
    MESSAGE_TYPE = 5
    ONLY_WHITE_TEXT = 6


@enum.unique
class FilterEntityType(enum.Enum):
    MENTION = (1, types.MessageEntityMention)
    HASHTAG = (2, types.MessageEntityHashtag)
    CASHTAG = (3, types.MessageEntityCashtag)
    BOT_COMMAND = (4, types.MessageEntityBotCommand)
    URL = (5, types.MessageEntityUrl)
    EMAIL = (6, types.MessageEntityEmail)
    PHONE_NUMBER = (7, types.MessageEntityPhone)
    BOLD = (8, types.MessageEntityBold)
    ITALIC = (9, types.MessageEntityItalic)
    UNDERLINE = (10, types.MessageEntityUnderline)
    STRIKETHROUGH = (11, types.MessageEntityStrike)
    SPOILER = (12, types.MessageEntitySpoiler)
    CODE = (13, types.MessageEntityCode)
    PRE = (14, types.MessageEntityPre)
    BLOCKQUOTE = (15, types.MessageEntityBlockquote)
    TEXT_LINK = (16, types.MessageEntityTextUrl)
    TEXT_MENTION = (17, types.MessageEntityMentionName)
    BANK_CARD = (18, types.MessageEntityBankCard)
    CUSTOM_EMOJI = (19, types.MessageEntityCustomEmoji)
    UNKNOWN = (20, types.MessageEntityUnknown)


@enum.unique
class FilterMessageType(enum.Enum):
    TEXT = (1, "message")
    REPLY = (2, "reply_to_msg_id")
    FORWARDED = (3, "fwd_from")
    AUDIO = (5, "audio")
    DOCUMENT = (6, "document")
    PHOTO = (7, "photo")
    STICKER = (8, "sticker")
    ANIMATION = (9, "gif")
    GAME = (10, "game")
    VIDEO = (11, "video")
    MEDIA_GROUP = (12, "is_group")
    VOICE = (13, "voice")
    VIDEO_NOTE = (14, "video_note")
    CONTACT = (15, "contact")
    LOCATION = (16, "geo")
    VENUE = (17, "venue")
    WEB_PAGE = (18, "web_preview")
    POLL = (19, "poll")
    DICE = (20, "dice")
    MENTIONED = (21, "mentioned")
    MEDIA = (22, "media")
    WITH_REPLY_MARKUP = (23, "reply_markup")
    VIA_BOT = (24, "via_bot")
    INVOICE = (25, "invoice")


FILTER_TYPES_BY_ID = {item.value: item.name for item in FilterType}
FILTER_ENTITY_TYPES_BY_ID = {item.value[0]: item.name for item in FilterEntityType}
FILTER_MESSAGE_TYPES_BY_ID = {item.value[0]: item.name for item in FilterMessageType}
