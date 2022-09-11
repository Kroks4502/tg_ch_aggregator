from peewee import *

db = SqliteDatabase('.db', pragmas={'foreign_keys': 1})


class BaseModel(Model):
    class Meta:
        database = db


class Category(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()

    def __str__(self):
        return self.title


class Source(BaseModel):
    tg_id = IntegerField(unique=True)
    title = CharField()
    category = ForeignKeyField(
        Category, backref='channels', on_delete='CASCADE')

    def __str__(self):
        return self.title

    def get_blacklist_hashtag(self) -> list:
        query = Filter.filter(content_type='hashtag', source=self)
        return [blacklist.pattern for blacklist in query]

    def get_blacklist_part_of_url(self) -> list:
        query = Filter.filter(content_type='part_of_url', source=self)
        return [blacklist.pattern for blacklist in query]

    def get_blacklist_part_of_text(self) -> list:
        query = Filter.filter(content_type='part_of_text', source=self)
        return [blacklist.pattern for blacklist in query]

    def get_blacklist_reply_markup(self) -> list:
        query = Filter.filter(content_type='reply_markup', source=self)
        return [blacklist.pattern for blacklist in query]

    @staticmethod
    def get_all_ids():
        return [ch.tg_id for ch in Source.select(Source.tg_id)]


FILTER_CONTENT_TYPES = ('hashtag', 'part_of_url', 'part_of_text')


class Filter(BaseModel):
    pattern = CharField()
    content_type = CharField()
    source = ForeignKeyField(
        Source, null=True, backref='blacklists', on_delete='CASCADE')

    def __str__(self):
        return self.pattern

    @staticmethod
    def global_hashtag() -> list:
        query = Filter.filter(content_type='hashtag', source=None)
        return [blacklist.pattern for blacklist in query]

    @staticmethod
    def global_part_of_url() -> list:
        query = Filter.filter(content_type='part_of_url', source=None)
        return [blacklist.pattern for blacklist in query]

    @staticmethod
    def global_part_of_text() -> list:
        query = Filter.filter(content_type='part_of_text', source=None)
        return [blacklist.pattern for blacklist in query]

    @staticmethod
    def global_reply_markup() -> list:
        query = Filter.filter(content_type='reply_markup', source=None)
        return [blacklist.pattern for blacklist in query]
