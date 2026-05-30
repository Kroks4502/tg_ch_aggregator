# CLAUDE.md

Документация проекта для агентов Claude Code. Читается автоматически в начале каждой сессии в этом репозитории.

## О проекте

**tg_ch_aggregator** — Telegram-агрегатор каналов. Пользовательский Telegram-клиент (userbot) слушает заданные «источники» (каналы-источники) и пересылает/перепечатывает сообщения в «категории» (каналы-агрегаторы). Управление выполняется через отдельного бота. Поддерживаются фильтрация сообщений, очистка текста по regex, дедупликация пересылок, а также правила уведомлений (counter/regex).

Язык кода — Python 3.13. Бизнес-комментарии и docstrings — на русском, имена идентификаторов — на английском. **Поддерживай это соглашение при правках.**

## Стек

- **Pyrogram** — через форк `pyrofork==2.3.68`. Два клиента: `user` (userbot) и `bot`. Плагины подключаются через `plugins=dict(root=...)`.
- **peewee 3** + **psycopg2-binary** + `playhouse.postgres_ext` (`PostgresqlExtDatabase`, `BinaryJSONField`/`JSONField`).
- **gevent** — psycopg2 пропатчен callback'ом для кооперативной многозадачности (см. [src/db.py](src/db.py)). Любая работа с БД должна происходить через `psql_db`.
- **APScheduler** (`AsyncIOScheduler`) — фоновые задачи (см. [src/scheduler/run.py](src/scheduler/run.py)).
- **yoyo-migrations** — миграции PostgreSQL в [migrations/](migrations/) (`*.sql`, иногда есть rollback-файлы). Конфиг: [yoyo.ini](yoyo.ini).
- **PostgreSQL 14+**, обычно 15-alpine в docker-compose.
- Тесты: **pytest** + `pytest-asyncio` (auto mode), есть `aiogram` для интеграционных тестов.

## Архитектура (что куда)

```
src/
├── main.py              # точка входа — connect db, gevent patch, scheduler, compose([bot, user])
├── clients.py           # инициализация pyrogram Client для user и bot
├── settings.py          # env vars, пути, DEVELOP_MODE, configure_logging
├── db.py                # psql_db (PostgresqlExtDatabase) + gevent-patch для psycopg2
├── models.py            # peewee-модели: User, Category, Source, Filter, MessageHistory,
│                        #   GlobalSettings, AlertRule, AlertHistory
├── filter_types.py      # enum'ы FilterType / FilterEntityType / FilterMessageType
│
├── alerts/              # правила уведомлений (counter + regex), их runtime-логика
├── scheduler/
│   ├── run.py           # сборка расписания (см. ниже)
│   └── jobs/            # отдельные job'ы (cleanup history, update channels/users, alerts, ...)
│
├── plugins/
│   ├── user/            # обработчики userbot'а — собственно агрегация сообщений
│   │   ├── sources_monitoring/   # on_message / on_edited_message / on_deleted_messages
│   │   ├── utils/                # cleanup, rewriter, senders, chats_locks, dump, ...
│   │   ├── exceptions.py         # иерархия MessageBaseError, логируют сами себя в __init__
│   │   └── types.py              # Operation (NEW/EDIT/DELETE) — используется в settings.py
│   └── bot/             # бот для администрирования
│       ├── router.py    # CallbackQueryRouter с декораторами .page / .wait_input / .command
│       ├── menu.py      # Menu (наследует utils/menu/MenuAbstract)
│       ├── buttons.py   # ButtonAdder
│       └── handlers/    # category / source / filter / alert_rules / cleanup / history / ...
│
├── common/              # переиспользуемое: db_json_fields, senders (admins),
│                        #   links, text, call_handlers
├── utils/               # menu, input_wait_manager, custom_filters (admin_only)
└── pyrogram_fork/       # локальные правки send_media_group / edit_message_media
```

Тесты в [tests/unit/](tests/unit/) и [tests/integration/](tests/integration/) (последние реально ходят в Telegram через `TEST_TELEGRAM_*`).

## Ключевые доменные сущности

- **Source** ([src/models.py:50](src/models.py)) — канал-источник. PK = Telegram chat id. Имеет `cleanup_list` (JSON-список regex), `is_rewrite` (перепечатывать или пересылать), `is_deleted` (soft-delete; фильтрация в `monitored_channels`).
- **Category** — канал-агрегатор. PK = Telegram chat id. `Source.category` (FK, `on_delete=CASCADE`).
- **Filter** — правило фильтрации для источника (или глобальное при `source IS NULL`). `type` — из `FilterType`.
- **MessageHistory** — основная транзакционная таблица. Хранит связь source↔category-сообщений, `media_group_id`, ссылку на repeat (`repeat_history`), `filter_id`, поля `created_at`/`edited_at`/`deleted_at`, и JSON `data` со снимками первого/последнего состояний (`first_message`, `last_message_without_error`, `last_message_with_error`). По ней работает дедупликация и регулярная очистка ([scheduler/jobs/cleanup_message_history.py](src/scheduler/jobs/cleanup_message_history.py)).
- **GlobalSettings** — KV-таблица. Ключ `cleanup_list` — глобальный список regex для очистки сообщений.
- **AlertRule** / **AlertHistory** — правила уведомлений (`type ∈ {counter, regex}`). Конфиги задаются датаклассами в [src/alerts/configs.py](src/alerts/configs.py). При срабатывании создаётся `AlertHistory` и через `common.call_handlers.call_callback_query_handler` вызывается обработчик бота, чтобы синтезировать «сообщение администратору» как будто пришёл callback.

## Пайплайн обработки сообщений (userbot)

[src/plugins/user/sources_monitoring/new_message.py](src/plugins/user/sources_monitoring/new_message.py) — образец паттерна:

1. Фильтр `custom_filters.monitored_channels & ~filters.service` — пускает только сообщения из активных Source.
2. `set_blocking(...)` — блокировка по `media_group_id or message.id`, чтобы избежать гонок (см. [utils/chats_locks.py](src/plugins/user/utils/chats_locks.py)).
3. `dump_message(...)` — опционально складывает JSON сообщения в `tests/dump_messages/` при `DUMP_MESSAGE_MODE`.
4. Для медиа-группы — `await message.get_media_group()` (это **первый await**, см. комментарий в коде; до него гонки купированы блокировкой).
5. Проверки: `get_repeated_history_id_or_none` (дедупликация по source/forward), `get_filter_id_or_none`. При совпадении — соответствующий `MessageBaseError`.
6. Если `source.is_rewrite=True`: `cleanup_message` → `add_header` → `cut_long_message` → `message.copy(...)`. Иначе `message.forward(...)`.
7. После отправки — заполняется `MessageHistory.category_*`, вызывается `check_message_by_regex_alert_rule`.
8. `finally`: снять блокировку, сохранить `history_obj.save()`, пометить чат прочитанным.

Похожий каркас в [edited_message.py](src/plugins/user/sources_monitoring/edited_message.py) и [deleted_messages.py](src/plugins/user/sources_monitoring/deleted_messages.py).

**Иерархия исключений** ([plugins/user/exceptions.py](src/plugins/user/exceptions.py)): все `MessageBaseError`-наследники **логируют сами себя в `__init__`** через `logging.log(...)`, и каждый знает свой `logging_level`. При добавлении нового — следовать той же схеме (`end_tmpl`, `logging_level`, `to_dict`).

## Бот: меню и роутер

Обработчики бота не используют декораторы Pyrogram напрямую — вместо них в [src/plugins/bot/router.py](src/plugins/bot/router.py) свой `CallbackQueryRouter` с тремя декораторами:

- `@router.page(path=..., admin_only=True, pagination=False, command=False, ...)` — обработчик callback'а по regex-пути. Можно опубликовать тот же handler как `/команду`, передав `command=True` (path `/a/b/` ↔ команда `/a_b`).
- `@router.wait_input(...)` — обработчик ожидаемого текстового ввода после нажатия кнопки. Подключается через `add_wait_for_input=...` другого page'а и `InputWaitManager` ([utils/input_wait_manager.py](src/utils/input_wait_manager.py)).
- `@router.command(commands=[...])` — обычная команда бота (например, `/start`, `/cancel`, см. [handlers/main.py](src/plugins/bot/handlers/main.py)).

Внутри handler'а собирается `Menu` (см. [plugins/bot/menu.py](src/plugins/bot/menu.py)), кнопки добавляются через `menu.add_button.*` ([buttons.py](src/plugins/bot/buttons.py)). Возвращаемая строка станет текстом сообщения; роутер сам решит, редактировать существующее или отправить новое (`menu.need_send_new_message`/`reply`).

Доступ для администраторов: `utils/custom_filters.admin_only` + `Menu.is_admin_user()` (читает `User.is_admin`).

## Scheduler

[src/scheduler/run.py](src/scheduler/run.py) при старте дожидается готовности обоих pyrogram-клиентов, затем:

- Одноразовые startup-job'ы: `set_user_bot_as_admin`, `processing_unread_messages`, `update_users_info`, `update_channels_info`.
- Периодические: `processing_unread_messages` (5 мин), `update_users_info` (180 мин), `update_channels_info` (180 мин), `cleanup_message_history` (CronTrigger каждый день в 00:00).
- `add_all_evaluation_counter_rule_job()` — регистрирует jobs под каждое `AlertRule(type='counter')`. При CRUD правил планировщик надо обновлять (см. вызовы в `plugins/bot/handlers/alert_rules/`).

`cleanup_message_history_job` удаляет строки старше `MESSAGE_HISTORY_RETENTION_MONTHS` месяцев (по умолчанию 6, env override), затем выполняет `VACUUM ANALYZE message_history` с временно включённым `autocommit=True`.

## Конфигурация и env

Все env'ы и пути — в [src/settings.py](src/settings.py). Обязательные: `TELEGRAM_API_ID/HASH/BOT_TOKEN`, `POSTGRES_*`. Спец-режимы:

- `DEVELOP_MODE="1"` — включает DEBUG-логи для root/peewee/apscheduler и INFO для pyrogram.
- `DEVELOP_MODE="bot"` — `IS_ONLY_BOT=True`: userbot стартует без плагинов, scheduler не запускается. Удобно для разработки только бота.
- `DUMP_MESSAGE_MODE=1` — все входящие сообщения userbot'а дампятся в `tests/dump_messages/{new,edited,deleted}_messages/`.
- `MESSAGE_HISTORY_RETENTION_MONTHS` — глубина истории (default 6, min 1). Парсер бросает `ValueError` на мусор/значения <1.

Шаблон env: [.env.template](.env.template). Сессии Pyrogram (`user.session`, `bot.session`) лежат в `sessions/` (создаются `create_tg_sessions.py`).

## Локальная разработка

Запуск только через docker-compose, скрипт-обёртка: [docker/docker-run.dev.sh](docker/docker-run.dev.sh). Все команды — `docker compose` (v2, plugin-форма; **не** `docker-compose`).

```bash
./docker/docker-run.dev.sh start                    # up -d
./docker/docker-run.dev.sh restart [service]
./docker/docker-run.dev.sh logs [service]
./docker/docker-run.dev.sh create_sessions          # интерактивно — создать user.session
./docker/docker-run.dev.sh build|stop|clean|ps
```

Entrypoint backend-контейнера ([docker/scripts/backend_entrypoint.sh](docker/scripts/backend_entrypoint.sh)):
1. Ждёт `pg_isready`.
2. Запускает `yoyo apply` против `postgresql://...` — миграции применяются автоматически при каждом старте.
3. Ждёт появления `sessions/user.session` и `sessions/bot.session`.
4. Запускает `python main.py` (cwd = `/app/src`).

Прод — отдельный compose [docker/docker-compose.prod.yml](docker/docker-compose.prod.yml), деплой через GitHub Actions: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) (билд → push в `ghcr.io` → SCP+SSH на сервер).

## Миграции

Новая миграция — новый файл `migrations/NNN-name.sql` (нумерация по порядку, сейчас последняя 022). Чистый SQL, можно DDL+DML. Опционально парный `*.rollback.sql`. Не редактируй уже применённые миграции — пиши новую.

При изменении модели в [src/models.py](src/models.py) — обязательно соответствующая миграция. peewee здесь **не** генерирует схему сама.

## Тесты и codestyle

```bash
pytest                 # см. pytest.ini: pythonpath=src ., asyncio_mode=auto
flake8                 # см. setup.cfg: max-line-length=120, max-complexity=10, исключения для black
black .                # target=py313, preview=True, exclude pyrogram_fork
isort . --settings setup.cfg
```

`pre-commit` гоняет isort + black + flake8 (+ ряд проверок pre-commit-hooks). CI [`.github/workflows/codestyle.yml`](.github/workflows/codestyle.yml) повторяет это на каждом push.

**Запрет `print`** — включён `flake8-print`. Везде использовать `logging`.

## Соглашения и подводные камни

- **gevent + psycopg2**: `db.patch_psycopg2()` вызывается **один раз** в `main.py` после `db.connect()`. Не вводи синхронные блокирующие вызовы в обход.
- **Блокировки сообщений** ([utils/chats_locks.py](src/plugins/user/utils/chats_locks.py)) — обязательны для любых новых хендлеров на чатах-источниках, иначе media-группы будут обрабатываться частично.
- **Pyrogram-форк**: используй `pyrogram_fork.send_media_group.SendMediaGroup.send_media_group` и `pyrogram_fork.edit_media_message.EditMessageMedia.edit_message_media` — обычные методы клиента в проекте перекрыты не везде.
- **JSONField encoder**: `BinaryJSONField` для `AlertRule.config`/`AlertHistory.data` инициализирован `DBJsonFieldEncoder.json_dumper` ([common/db_json_fields.py](src/common/db_json_fields.py)) — поддерживает датаклассы из [alerts/configs.py](src/alerts/configs.py). Не подменяй на голый `json.dumps`.
- **soft-delete Source**: фильтр `is_deleted=False` живёт в `monitored_channels`. Не запрашивай Source напрямую без оглядки на это поле в местах, где смысл — «активные источники».
- **Идентификаторы PK** = Telegram chat id (`BigIntegerField`, без `autoincrement`) для `User`, `Category`, `Source`. Не пытайся подменять на `BigAutoField`.
- **Поведение бота при ValueError**: декораторы `wait_input/command/_page_as_command` в `router.py` ловят `ValueError` и шлют её `str(error)` пользователю как текст. Это удобный способ возвращать пользовательские ошибки валидации — не оборачивай их в try/except внутри handler'а зря.
- **Локализация**: тексты для пользователя — на русском. Логи — обычно тоже на русском (так уже принято в проекте).

## Полезные точки входа при правках

| Хочу сделать | Куда смотреть |
| --- | --- |
| Новый тип фильтра | [src/filter_types.py](src/filter_types.py) + хендлеры в [plugins/bot/handlers/filter/](src/plugins/bot/handlers/filter/) + использование в [plugins/user/sources_monitoring/common.py](src/plugins/user/sources_monitoring/common.py) |
| Новый тип alert | [src/alerts/](src/alerts/) + handlers в [plugins/bot/handlers/alert_rules/](src/plugins/bot/handlers/alert_rules/) + регистрация в [scheduler/run.py](src/scheduler/run.py) или прямой вызов в pipeline |
| Новый периодический job | [src/scheduler/jobs/](src/scheduler/jobs/) + регистрация в `scheduler/run.py:startup_job` |
| Новая страница меню бота | [src/plugins/bot/handlers/](src/plugins/bot/handlers/) + кнопка в [buttons.py](src/plugins/bot/buttons.py) |
| Изменение схемы БД | модель в [src/models.py](src/models.py) **и** новая миграция в [migrations/](migrations/) |
| Новая регулярная очистка сообщений | глобально — `GlobalSettings(key='cleanup_list')`; для конкретного источника — `Source.cleanup_list` (см. [utils/cleanup.py](src/plugins/user/utils/cleanup.py)) |
