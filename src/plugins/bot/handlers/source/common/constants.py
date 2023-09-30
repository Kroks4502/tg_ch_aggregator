from plugins.bot.constants.text import CONF_DEL_TEXT_TPL, ERROR_TEXT

# TITLE

SINGULAR_SOURCE_TITLE = "Источник"
PLURAL_SOURCE_TITLE = "Источники"

# TEXT

SINGULAR_SOURCE_TEXT = SINGULAR_SOURCE_TITLE.lower()
SOURCE_TEXT = "для источника"

# ACTION

ACTION_ENTER_SOURCE_LINK = "Введи публичное имя канала или частную ссылку"
ACTION_ENTER_SOURCE_ALIAS = "Введи псевдоним"

# QUESTION

QUESTION_CONF_DEL = CONF_DEL_TEXT_TPL.format(SINGULAR_SOURCE_TITLE.lower())
QUESTION_SELECT_NEW_CATEGORY = (
    "Ты **меняешь категорию** у источника. Выбери новую категорию:"
)

SUCCESS_ACTION_MODE_SWITCHING_TEXT = "переключен в режим {} сообщений"

# ERROR

ERROR_JOIN_CHAT_FAILED = ERROR_TEXT.format(
    text="Основной клиент не может подписаться на канал"
)
ERROR_EXISTED_SOURCE = ERROR_TEXT.format(text="Источник уже добавлен")
