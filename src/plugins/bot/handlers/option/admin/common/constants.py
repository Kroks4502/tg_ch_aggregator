from plugins.bot.constants.text import CONF_DEL_TEXT_TPL, DIALOG, ERROR_TEXT

# TITLE

SINGULAR_USER_TITLE = "Администратор"
PLURAL_USER_TITLE = "Администраторы"

USER_DETAIL_TITLE = f"{SINGULAR_USER_TITLE} {{}}"

# QUESTION

QUESTION_CONF_DEL = CONF_DEL_TEXT_TPL.format("администратора")

DIALOG_ADD_TEXT = DIALOG.format(
    doing="добавляешь нового администратора.",
    action="Введи публичное имя пользователя",
)

# ERROR

ERROR_NOT_USER = ERROR_TEXT.format(text="Это не пользователь")
ERROR_USER_IS_ADMIN = ERROR_TEXT.format(text="Этот пользователь уже администратор")
