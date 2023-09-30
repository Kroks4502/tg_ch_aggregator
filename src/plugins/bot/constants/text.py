from plugins.bot.constants import commands as comm
from plugins.bot.constants import symbols as sym

MAIN_MENU_TEXT = "**Агрегатор каналов**"

MENU_TEXT_TITLE = "**{}**"
MENU_TEXT_PARAM = "— {}: {}"
MENU_TEXT_CONTENT = "\n{}"
MENU_TEXT_QUESTION = "\n> {}"


SUCCESS_TEXT = f"{sym.SUCCESS} {{text}}"
ERROR_TEXT = f"{sym.ERROR} {{text}}"

DIALOG = f"ОК. Ты {{doing}}\n\n**{{action}}** или {comm.CANCEL_COMMAND}"

CONF_DEL_TEXT_TPL = "Ты **удаляешь** {}!"

CATEGORY_NAME_TPL = "{} | Aggregator"

QUESTION_EDIT_PAGE = "Что ты хочешь изменить?"

ERROR_UNKNOWN = ERROR_TEXT.format(text="Что-то пошло не так")
ERROR_NOT_CHANNEL = ERROR_TEXT.format(text="Это не канал")
ERROR_INVALID_REGEX = ERROR_TEXT.format(text="Невалидное регулярное выражение")
ERROR_INVALID_LENGTH = ERROR_TEXT.format(
    text="Количество символов не должно превышать {length}"
)
ERROR_MESSAGE_IS_NOT_PHOTO = ERROR_TEXT.format(
    text="Допустимо только сообщение с изображением"
)
ERROR_MESSAGE_IS_NOT_TEXT = ERROR_TEXT.format(
    text="Допустимо только текстовое сообщение"
)
