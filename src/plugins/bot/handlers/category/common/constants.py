from plugins.bot.constants.text import CONF_DEL_TEXT_TPL

# TITLE

SINGULAR_CATEGORY_TITLE = "Категория"
PLURAL_CATEGORY_TITLE = "Категории"

# TEXT

ADD_CATEGORY_TEXT = (
    "добавляешь новую категорию, которая будет получать сообщения из источников. Будет"
    " создан новый канал-агрегатор."
)
CATEGORY_TEXT = "категории {}"
EDIT_CATEGORY_DESC_TEXT = "меняешь описание канала"
EDIT_CATEGORY_TITLE_TEXT = "меняешь название канала"
EDIT_CATEGORY_PHOTO_TEXT = "меняешь изображение канала"

# SUCCESS TEXT

SUCCESS_CATEGORY_EDIT_DESC_TEXT = "получила новое описание `{0}` вместо `{1}`"
SUCCESS_CATEGORY_EDIT_PHOTO_TEXT = "получила новое изображение"
SUCCESS_CATEGORY_EDIT_TITLE_TEXT = "получила новое название `{0}` вместо `{1}`"

# ACTION

ACTION_ENTER_CATEGORY_NAME = "Введи название категории"
ACTION_ENTER_CATEGORY_DESC = "Введи новое описание"
ACTION_SEND_CATEGORY_PHOTO = "Отправь новое изображение"

# QUESTION

QUESTION_CONF_DEL = CONF_DEL_TEXT_TPL.format("категорию")
