from datetime import datetime

from peewee import *

from models.types import FilterType
from settings import DATABASE


class BaseModel(Model):
    _is_actual_cache = False
    _cache = None

    class Meta:
        database = DATABASE

    @classmethod
    def get_cache(cls, **where) -> dict:
        cls._update_cache()

        conditions = {}
        if where:
            for i, field_name in enumerate(cls._meta.sorted_field_names):
                if field_name in where:
                    conditions[i] = where[field_name]
            if len(where) != len(conditions):
                raise Exception(f'Одного из имен полей нет в модели {cls.__name__}')

        for row in cls._cache:
            if all(True if row[i] == value else False for i, value in conditions.items()):
                yield {field_name: row[i] for i, field_name in enumerate(cls._meta.sorted_field_names)}

    @classmethod
    def _update_cache(cls):
        if not cls._is_actual_cache:
            cls._cache = tuple(cls.select().tuples())
            cls._is_actual_cache = True

    @classmethod
    def clear_actual_cache(cls):
        cls._is_actual_cache = False


class ChannelModel(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()

    def __str__(self):
        return self.title


class Category(ChannelModel):
    ...


class Source(ChannelModel):
    category = ForeignKeyField(
        Category, backref='sources', on_delete='CASCADE')
    _cache_monitored_channels = None

    @classmethod
    def get_cache_monitored_channels(cls):
        cls._update_cache()
        return cls._cache_monitored_channels

    @classmethod
    def _update_cache(cls):
        if not cls._is_actual_cache:
            cls._cache = tuple(cls.select().tuples())
            index = 0
            for field_name in cls._meta.sorted_field_names:
                if field_name == 'tg_id':
                    break
                index += 1
            cls._cache_monitored_channels = {row[index] for row in cls._cache}
            cls._is_actual_cache = True


class Filter(BaseModel):
    pattern = CharField()
    type = IntegerField(choices=[(filter_type.name, filter_type.value)
                                 for filter_type in FilterType])
    source = ForeignKeyField(
        Source, null=True, backref='filters', on_delete='CASCADE')

    def __str__(self):
        return self.pattern


class Admin(BaseModel):
    tg_id = IntegerField(unique=True)
    username = CharField()

    def __str__(self):
        return self.username


class MessageHistoryModel(BaseModel):
    date = DateTimeField(default=datetime.now)
    source = ForeignKeyField(Source)
    source_message_id = IntegerField()
    source_message_edited = BooleanField(default=False)
    source_message_deleted = BooleanField(default=False)
    media_group = CharField()


class FilterMessageHistory(MessageHistoryModel):
    filter = ForeignKeyField(Filter, backref='history', on_delete='CASCADE')


class CategoryMessageHistory(MessageHistoryModel):
    forward_from_chat_id = IntegerField(null=True)
    forward_from_message_id = IntegerField(null=True)
    category = ForeignKeyField(Category, on_delete='CASCADE')
    message_id = IntegerField()
    rewritten = BooleanField()
    deleted = BooleanField(default=False)



