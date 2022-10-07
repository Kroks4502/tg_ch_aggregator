import enum


@enum.unique
class FilterTypes(enum.Enum):
    HASHTAG = 1
    URL = 2
    TEXT = 3
    REPLY_MARKUP = 4
    ENTITIES_TYPES = 5
