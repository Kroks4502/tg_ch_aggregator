import enum


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
    MENTION = 1
    HASHTAG = 2
    CASHTAG = 3
    BOT_COMMAND = 4
    URL = 5
    EMAIL = 6
    PHONE_NUMBER = 7
    BOLD = 8
    ITALIC = 9
    UNDERLINE = 10
    STRIKETHROUGH = 11
    SPOILER = 12
    CODE = 13
    PRE = 14
    BLOCKQUOTE = 15
    TEXT_LINK = 16
    TEXT_MENTION = 17
    BANK_CARD = 18
    CUSTOM_EMOJI = 19
    UNKNOWN = 20


@enum.unique
class FilterMessageType(enum.Enum):
    TEXT = (1, "text")
    REPLY = (2, "reply_to_message_id")
    FORWARDED = (3, "forward_date")
    CAPTION = (4, "caption")
    AUDIO = (5, "audio")
    DOCUMENT = (6, "document")
    PHOTO = (7, "photo")
    STICKER = (8, "sticker")
    ANIMATION = (9, "animation")
    GAME = (10, "game")
    VIDEO = (11, "video")
    MEDIA_GROUP = (12, "media_group_id")
    VOICE = (13, "voice")
    VIDEO_NOTE = (14, "video_note")
    CONTACT = (15, "contact")
    LOCATION = (16, "location")
    VENUE = (17, "venue")
    WEB_PAGE = (18, "web_page")
    POLL = (19, "poll")
    DICE = (20, "dice")
    MENTIONED = (21, "mentioned")
    MEDIA = (22, "media")
    WITH_REPLY_MARKUP = (23, "reply_markup")
    VIA_BOT = (24, "via_bot")


FILTER_TYPES_BY_ID = {item.value: item.name for item in FilterType}
FILTER_ENTITY_TYPES_BY_ID = {item.value: item.name for item in FilterEntityType}
FILTER_MESSAGE_TYPES_BY_ID = {item.value[0]: item.name for item in FilterMessageType}
