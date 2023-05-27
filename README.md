# Агрегатор телеграм каналов

[![Deploy Telegram Channel Aggregator](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/main.yml/badge.svg)](https://github.com/Kroks4502/tg_ch_aggregator/actions/workflows/main.yml)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pyrogram](https://img.shields.io/badge/Pyrogram-ff1709?style=for-the-badge&color=bf431d)

...

## Возможности
...

## Технологии
- Python 3.10
- Pyrogram 2.0
- Peewee 3.15

## Запуск проекта
1. Клонировать репозиторий
2. Создать .env файл по шаблону [.env.template](.env.template)
3. Выполнить создание таблиц БД c [create_db_tables.py](create_db_tables.py) по текущим моделям, либо применить все миграции
    ```shell
    apt install yoyo
    yoyo apply --database postgresql://{{ db_user }}:{{ db_pass }}@localhost/{{ db_name }}
    ```
4. Пройти авторизацию в Telegram [create_tg_sessions.py](create_tg_sessions.py)


## Как использовать
...

## ToDo

- [ ] Написать readme
