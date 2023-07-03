from datetime import datetime

from peewee import (
    BigAutoField,
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    Model,
    SmallIntegerField,
)
from playhouse.postgres_ext import BinaryJSONField, JSONField

from config import DATABASE
from filter_types import FilterType


class BaseModel(Model):
    _is_actual_cache = False
    _cache = None

    class Meta:
        database = DATABASE

    @classmethod
    def get_cache(cls, **where):
        cls._update_cache()

        conditions = {}
        if where:
            for i, field_name in enumerate(cls._meta.sorted_field_names):
                if field_name in where:
                    conditions[i] = where[field_name]
            if len(where) != len(conditions):
                raise Exception(f'Одного из имен полей нет в модели {cls.__name__}')

        for row in cls._cache:
            if all(
                True if row[i] == value else False for i, value in conditions.items()
            ):
                yield {
                    field_name: row[i]
                    for i, field_name in enumerate(cls._meta.sorted_field_names)
                }

    @classmethod
    def _update_cache(cls):
        if not cls._is_actual_cache:
            cls._cache = tuple(cls.select().tuples())
            cls._is_actual_cache = True

    @classmethod
    def clear_actual_cache(cls):
        cls._is_actual_cache = False


class GlobalSettings(BaseModel):
    key = CharField(primary_key=True, unique=True)
    value = JSONField()

    class Meta:
        primary_key = False
        table_name = 'global_settings'


class Category(BaseModel):
    id = BigIntegerField(primary_key=True)
    title = CharField()


class Source(BaseModel):
    id = BigIntegerField(primary_key=True)
    title = CharField()
    category = ForeignKeyField(Category, backref='sources', on_delete='CASCADE')

    # Список регулярных выражений для очистки сообщений и их перепечатывания
    cleanup_list = JSONField(default=[])

    # Формировать новое сообщение (True) или пересылать сообщение (False)
    is_rewrite = BooleanField(default=False)

    _cache_monitored_channels = None

    @classmethod
    def get_cache_monitored_channels(cls) -> set:
        cls._update_cache()
        return cls._cache_monitored_channels

    @classmethod
    def _update_cache(cls):
        if not cls._is_actual_cache:
            cls._cache = tuple(cls.select().tuples())
            index = 0
            for field_name in cls._meta.sorted_field_names:
                if field_name == 'id':
                    break
                index += 1
            cls._cache_monitored_channels = {row[index] for row in cls._cache}
            cls._is_actual_cache = True


class Filter(BaseModel):
    pattern = CharField()
    type = SmallIntegerField(
        choices=[(filter_type.name, filter_type.value) for filter_type in FilterType]
    )
    source = ForeignKeyField(Source, null=True, backref='filters', on_delete='CASCADE')


class Admin(BaseModel):
    id = BigIntegerField(primary_key=True)
    username = CharField()

    _cache_admins_tg_ids = None

    @classmethod
    def get_cache_admins_tg_ids(cls):
        cls._update_cache()
        return cls._cache_admins_tg_ids

    @classmethod
    def _update_cache(cls):
        if not cls._is_actual_cache:
            cls._cache = tuple(cls.select().tuples())
            index = 0
            for field_name in cls._meta.sorted_field_names:
                if field_name == 'id':
                    break
                index += 1
            cls._cache_admins_tg_ids = {row[index] for row in cls._cache}
            cls._is_actual_cache = True

    def __str__(self):
        return self.username


class MessageHistory(BaseModel):
    id = BigAutoField(primary_key=True)

    source = ForeignKeyField(
        Source, backref='history', on_delete='CASCADE'
    )  # source_id
    source_message_id = BigIntegerField()
    source_media_group_id = CharField(default=None, null=True)
    source_forward_from_chat_id = BigIntegerField(default=None, null=True)
    source_forward_from_message_id = BigIntegerField(default=None, null=True)

    category = ForeignKeyField(
        Category, backref='history', on_delete='CASCADE'
    )  # category_id
    category_message_id = BigIntegerField(default=None, null=True)
    category_media_group_id = CharField(default=None, null=True)
    category_message_rewritten = BooleanField(default=None, null=True)

    repeat_history = ForeignKeyField(
        'self', on_delete='SET NULL', null=True, default=None
    )
    filter = ForeignKeyField(
        Filter, backref='history', on_delete='SET NULL', null=True, default=None
    )

    created_at = DateTimeField(default=datetime.now)
    edited_at = DateTimeField(default=None, null=True)
    deleted_at = DateTimeField(default=None, null=True)

    data = BinaryJSONField()

    class Meta:
        table_name = 'message_history'
