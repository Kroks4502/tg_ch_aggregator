# Агрегатор телеграм каналов

[![Deploy Telegram Channel Aggregator](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/main.yml/badge.svg)](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/main.yml)

[![Python][Python-badge]][Python-url]
[![Pyrogram][Pyrogram-badge]][Pyrogram-url]
[![Postgres][Postgres-badge]][Postgres-url]

Создавайте свои ленты новостей из телеграм каналов!

## Возможности

- Создание категорий для каналов, в которые будут попадать сообщения из источников
- Фильтрация сообщений из источников для предотвращения пересылки нежелательных сообщений в категориях
  по хештегам, ссылкам, тексту, сущностям (entity_type) или типу сообщений
- Полное управление категориями, источниками и фильтрами с помощью бота

## Технологии

- Python 3.10
- Pyrogram 2.0
- Peewee 3.15

## Запуск проекта

1. Клонировать репозиторий
2. Создать .env файл согласно шаблону [.env.template](.env.template)
3. Выполнить создание таблиц БД c [create_db_tables.py](create_db_tables.py) по текущим моделям, либо применить все
   миграции
    ```shell
    apt install yoyo
    yoyo apply --database postgresql://{{ db_user }}:{{ db_pass }}@localhost/{{ db_name }}
    ```
4. Пройти авторизацию в Telegram [create_tg_sessions.py](create_tg_sessions.py)

[Python-url]: https://www.python.org/
[Python-badge]: https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54

[Pyrogram-url]: https://docs.pyrogram.org/
[Pyrogram-badge]: https://img.shields.io/badge/Pyrogram-ff1709?style=for-the-badge&logo=telegram&color=bf431d

[Postgres-url]: https://www.postgresql.org/
[Postgres-badge]: https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white
