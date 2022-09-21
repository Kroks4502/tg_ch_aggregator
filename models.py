from peewee import *

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


class Category(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()

    def __str__(self):
        return self.title


class Source(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()
    category = ForeignKeyField(
        Category, backref='sources', on_delete='CASCADE')

    def __str__(self):
        return self.title

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

    def __str__(self):
        return self.pattern

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


class Admin(BaseModel):
    tg_id = IntegerField(unique=True)
    username = CharField()

    def __str__(self):
        return self.username
