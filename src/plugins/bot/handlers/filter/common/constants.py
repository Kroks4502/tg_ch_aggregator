from plugins.bot.constants.text import CONF_DEL_TEXT_TPL

# TITLE

_NEW = "Новый"
SINGULAR_FILTER_TITLE = "Фильтр"
SINGULAR_COMMON_FILTER_TITLE = f"Общий {SINGULAR_FILTER_TITLE.lower()}"

NEW_FILTER_TITLE = f"{_NEW} {SINGULAR_FILTER_TITLE.lower()}"
NEW_COMMON_FILTER_TITLE = f"{_NEW} {SINGULAR_COMMON_FILTER_TITLE.lower()}"

PLURAL_FILTER_TITLE = "Фильтры"
PLURAL_COMMON_FILTER_TITLE = f"Общие {PLURAL_FILTER_TITLE.lower()}"

ALL_PLURAL_FILTER_TITLE = f"Все {PLURAL_FILTER_TITLE.lower()}"

# TEXT

SINGULAR_FILTER_TEXT = SINGULAR_FILTER_TITLE.lower()
SINGULAR_COMMON_FILTER_TEXT = SINGULAR_COMMON_FILTER_TITLE.lower()

SOURCE_TEXT = "для источника {}"
FILTER_TYPE_TEXT = "типа **{}**"
FILTER_PATTERN_TEXT = "c паттерном `{}`"

FILTER_NOT_FOUND = "Фильтр не найден"

# STATISTIC TEXT
STATISTIC_FILTER_TITLE = "Статистика фильтрации за {} д."
STATISTIC_FILTER_COMMON_TITLE = f"Общая {STATISTIC_FILTER_TITLE.lower()}"

STATISTIC_FILTER_DATA_NOT_FOUND = "__Данные отсутствуют__"
STATISTIC_FILTER_TOP_10 = "**Топ-10**:\n{}"
STATISTIC_FILTER_ANTI_TOP_10 = "**Анти-топ-10**:\n{}"

STATISTIC_FILTER_LINE = "{amount}: /f_{id} {type} `{pattern}`"

# SUCCESS TEXT

SUCCESS_FILTER_PATTERN_ADD_TEXT = f"{FILTER_PATTERN_TEXT} создан"
SUCCESS_FILTER_PATTERN_DEL_TEXT = f"{FILTER_PATTERN_TEXT} удален"
SUCCESS_FILTER_PATTERN_EDIT_TEXT = "получил новый паттерн `{0}` вместо `{1}`"

# ACTION

ACTION_ENTER_PATTERN = "Введи паттерн"

# QUESTION

QUESTION_SELECT_PATTERN = "Выбери паттерн"
QUESTION_CONF_DEL = CONF_DEL_TEXT_TPL.format(SINGULAR_FILTER_TITLE.lower())
