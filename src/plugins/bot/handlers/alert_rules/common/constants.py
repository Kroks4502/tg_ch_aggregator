from plugins.bot.constants.text import CONF_DEL_TEXT_TPL, ERROR_TEXT

# TITLE

_NEW = "Новое"
SINGULAR_ALERT_RULE_TITLE = "Правило уведомления"
SINGULAR_COMMON_ALERT_RULE_TITLE = f"Общее {SINGULAR_ALERT_RULE_TITLE.lower()}"

NEW_ALERT_RULE_TITLE = f"{_NEW} {SINGULAR_ALERT_RULE_TITLE.lower()}"
NEW_COMMON_ALERT_RULE_TITLE = f"{_NEW} {SINGULAR_COMMON_ALERT_RULE_TITLE.lower()}"

PLURAL_ALERT_RULE_TITLE = "Правила уведомления"
PLURAL_COMMON_ALERT_RULE_TITLE = f"Общие {PLURAL_ALERT_RULE_TITLE.lower()}"

ALERT_RULE_COUNTER = "Счётчик сообщений"
ALERT_RULE_REGEX = "Регулярное выражение"

# TEXT

SINGULAR_ALERT_RULE_TEXT = SINGULAR_ALERT_RULE_TITLE.lower()
SINGULAR_COMMON_ALERT_RULE_TEXT = SINGULAR_COMMON_ALERT_RULE_TITLE.lower()

NEW_ALERT_RULE_TEXT = NEW_ALERT_RULE_TITLE.lower()

USER_TEXT = "пользователя {}"
JOB_INTERVAL_TEXT = "с проверкой раз в {job_interval} мин."
COUNT_INTERVAL_TEXT = "окном проверки {count_interval} мин."
THRESHOLD_TEXT = "порогом срабатывания {threshold} шт."
REGEX_TEXT = "на основе регулярного выражения `{regex}`"
CATEGORY_TEXT = "для категории {}"

LAST_FIRED_TEXT = "⏮ Последнее срабатывание"

# ACTION

ACTION_ENTER_REGEX = "Введи регулярное выражение"
ACTION_ENTER_THRESHOLD = "Введи количество сообщений для срабатывания уведомления"

# QUESTION

QUESTION_CONF_DEL = CONF_DEL_TEXT_TPL.format(SINGULAR_ALERT_RULE_TITLE.lower())
QUESTION_COUNT_INTERVAL = (
    "За сколько последних минут будет выполняться проверка количества сообщений?"
)
QUESTION_JOB_INTERVAL = "Как часто будет выполнятся проверка правила?"

# ERRORS

ERROR_INVALID_THRESHOLD = ERROR_TEXT.format(
    text="Невалидный порог срабатывания уведомления"
)
QUESTION_SELECT_ALERT_RULE_TYPE = "Выбери тип правила"
