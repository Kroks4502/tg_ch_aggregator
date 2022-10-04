import enum
from datetime import datetime

from peewee import *

from initialization import user

db = SqliteDatabase('.db', pragmas={'foreign_keys': 1})


class BaseModel(Model):
    __is_actual_cache = False
    __cache = {}

    class Meta:
        database = db

    @classmethod
    def get_cache(cls, *fields, **where) -> dict:
        cls.__update_cache()

        if 'id' in where:
            db_id = where.pop('id')
            data = cls.__cache[db_id]
            if not all([data[key] == value for key, value in where.items()]):
                return {}
            return {db_id: {field: data[field] for field in fields}
                    if fields else data}

        selections_from_data = {}
        for db_id, data in cls.__cache.items():
            if all([data[key] == value for key, value in where.items()]):
                selections_from_data.update({
                    db_id: {field: data[field] for field in fields}
                    if fields else data
                })
        return selections_from_data

    @classmethod
    def get_cache_all_field(cls, field, **where):
        cls.__update_cache()
        return {value[field] for key, value in cls.get_cache(**where).items()}

    @classmethod
    def __update_cache(cls):
        if not cls.__is_actual_cache:
            cls.__cache = {item.pop('id'): item
                           for item in cls.select().dicts()}
            cls.__is_actual_cache = True

    @classmethod
    def clear_actual_cache(cls):
        cls.__is_actual_cache = False


class ChannelModel(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()

    async def get_formatted_link(self) -> str:
        chat = await user.get_chat(self.tg_id)
        if chat.username:
            return f'[{chat.title}](https://{chat.username}.t.me)'
        if chat.invite_link:
            return f'[{chat.title}]({chat.invite_link})'
        return chat.title

    def __str__(self):
        return self.title


class Category(ChannelModel):
    ...


class Source(ChannelModel):
    category = ForeignKeyField(
        Category, backref='sources', on_delete='CASCADE')


@enum.unique
class FilterContentTypesChoices(enum.Enum):
    HASHTAG = 1
    URL = 2
    TEXT = 3
    REPLY_MARKUP = 4
    ENTITIES_TYPES = 5


class Filter(BaseModel):
    pattern = CharField()
    type = IntegerField(choices=[(content_type.name, content_type.value)
                                 for content_type in FilterContentTypesChoices])
    source = ForeignKeyField(
        Source, null=True, backref='filters', on_delete='CASCADE')

    def __str__(self):
        return self.pattern


class Admin(BaseModel):
    tg_id = IntegerField(unique=True)
    username = CharField()

    async def get_formatted_link(self) -> str:
        chat = await user.get_chat(self.tg_id)
        if chat.username:
            return f'[{chat.username}](https://{chat.username}.t.me)'
        full_name = (f'{chat.first_name + " " if chat.first_name else ""}'
                     f'{chat.last_name + " " if chat.last_name else ""}')
        if full_name:
            return (f'{full_name} ({self.tg_id})'
                    if full_name else f'{self.tg_id}')
        return str(self.tg_id)

    def __str__(self):
        return self.username


class MessageHistoryModel(BaseModel):
    source = ForeignKeyField(Source)
    source_message_id = IntegerField()
    is_media_group = BooleanField()
    date = DateTimeField(default=datetime.now)


class FilterMessageHistory(MessageHistoryModel):
    filter = ForeignKeyField(Filter, backref='history', on_delete='CASCADE')


class CategoryMessageHistory(MessageHistoryModel):
    forward_from_chat_id = IntegerField(null=True)
    forward_from_message_id = IntegerField(null=True)
    category = ForeignKeyField(Category, on_delete='CASCADE')
    message_id = IntegerField()
    rewritten = BooleanField()
    deleted = BooleanField(default=False)


db.create_tables(
    [
        Category, Source, Filter, Admin,
        FilterMessageHistory, CategoryMessageHistory
    ]
)
