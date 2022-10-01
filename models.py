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
    def get_cache(cls, *fields, **where):
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
                           for item in Source.select().dicts()}
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

    def get_filter_patterns(self, content_type):
        query = Filter.filter(content_type=content_type, source=self)
        return [f.pattern for f in query]

    def get_filter_hashtag(self) -> list:
        return self.get_filter_patterns('hashtag')

    def get_filter_part_of_url(self) -> list:
        return self.get_filter_patterns('part_of_url')

    def get_filter_part_of_text(self) -> list:
        return self.get_filter_patterns('part_of_text')

    def get_filter_reply_markup(self) -> list:
        return self.get_filter_patterns('reply_markup')


FILTER_CONTENT_TYPES = ('hashtag', 'part_of_url', 'part_of_text',
                        'reply_markup')


class Filter(BaseModel):
    pattern = CharField()
    content_type = CharField()
    source = ForeignKeyField(
        Source, null=True, backref='filters', on_delete='CASCADE')

    @classmethod
    def get_global_patterns(cls, content_type) -> list:
        query = cls.filter(content_type=content_type, source=None)
        return [f.pattern for f in query]

    @classmethod
    def global_hashtag_patterns(cls) -> list:
        return cls.get_global_patterns('hashtag')

    @classmethod
    def global_part_of_url_patterns(cls) -> list:
        return cls.get_global_patterns('part_of_url')

    @classmethod
    def global_part_of_text_patterns(cls) -> list:
        return cls.get_global_patterns('part_of_text')

    @classmethod
    def global_reply_markup_patterns(cls) -> list:
        return cls.get_global_patterns('reply_markup')

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
    source = ForeignKeyField(Source, on_delete='CASCADE')
    source_message_id = IntegerField()
    is_media_group = BooleanField()


class FilterMessageHistory(MessageHistoryModel):
    filter = ForeignKeyField(Filter, backref='history')


class CategoryMessageHistory(MessageHistoryModel):
    category_message_id = IntegerField()
    rewritten = BooleanField()
    edited = BooleanField(default=False)
    deleted = BooleanField(default=False)
    date = DateTimeField(default=datetime.now)


db.create_tables(
    [
        Category, Source, Filter, Admin,
        FilterMessageHistory, CategoryMessageHistory
    ]
)
