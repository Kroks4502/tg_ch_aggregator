"""
Контракт callback-путей меню бота для внешних подсистем.

Внешние модули (alerts, scheduler, плагин userbot'а) формируют callback_data
кнопок, чтобы переадресовывать администратора в конкретный пункт меню.
Чтобы они не зависели от `plugins.bot.*`, путь-константы живут здесь.

Соответствующие handler'ы регистрируются в `plugins/bot/handlers/**`,
их `@router.page(path=...)` использует те же шаблоны.
"""

ALERT_DETAIL_PATH = "/a/{alert_id}/"
ALERT_RULE_DETAIL_PATH = "/r/{rule_id}/"
ALERT_LIST_PATH = f"{ALERT_RULE_DETAIL_PATH}a/"

CATEGORY_DETAIL_PATH = "/c/{category_id}/"
SOURCE_DETAIL_PATH = "/s/{source_id}/"
