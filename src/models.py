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

from common.db_json_fields import DBJsonFieldEncoder
from db import psql_db
from filter_types import FilterType


class BaseModel(Model):
    class Meta:
        database = psql_db


class GlobalSettings(BaseModel):
    key = CharField(primary_key=True, unique=True)
    value = JSONField()

    class Meta:
        primary_key = False
        table_name = "global_settings"


class User(BaseModel):
    id = BigIntegerField(primary_key=True)
    username = CharField()
    is_admin = BooleanField(default=False)
    added_at = DateTimeField(default=datetime.now)
    last_interaction_at = DateTimeField(default=datetime.now)

    def __str__(self):
        return str(self.username)


class Category(BaseModel):
    id = BigIntegerField(primary_key=True)
    title = CharField()


class Source(BaseModel):
    id = BigIntegerField(primary_key=True)
    title = CharField()
    title_alias = CharField()
    category = ForeignKeyField(Category, backref="sources", on_delete="CASCADE")

    # Список регулярных выражений для очистки сообщений и их перепечатывания
    cleanup_list = JSONField(default=[])

    # Формировать новое сообщение (True) или пересылать сообщение (False)
    is_rewrite = BooleanField(default=False)


class Filter(BaseModel):
    pattern = CharField()
    type = SmallIntegerField(
        choices=[(filter_type.name, filter_type.value) for filter_type in FilterType]
    )
    source = ForeignKeyField(Source, null=True, backref="filters", on_delete="CASCADE")


class AlertRule(BaseModel):
    user = ForeignKeyField(User, backref="alerts", on_delete="CASCADE", index=True)
    category = ForeignKeyField(
        Category,
        backref="alerts",
        on_delete="CASCADE",
        index=True,
        null=True,
    )
    type = CharField(max_length=32)  # counter | regex
    config = BinaryJSONField(dumps=DBJsonFieldEncoder.json_dumper)

    class Meta:
        table_name = "alert_rule"


class AlertHistory(BaseModel):
    category = ForeignKeyField(
        Category,
        backref="alerts_history",
        on_delete="CASCADE",
        index=True,
        null=True,
    )
    fired_at = DateTimeField(default=datetime.now)
    data = BinaryJSONField(dumps=DBJsonFieldEncoder.json_dumper)
    alert_rule = ForeignKeyField(
        AlertRule,
        backref="history",
    )

    class Meta:
        table_name = "alert_history"


class MessageHistory(BaseModel):
    id = BigAutoField(primary_key=True)

    source = ForeignKeyField(Source, backref="history", on_delete="CASCADE")
    source_message_id = BigIntegerField()
    source_media_group_id = CharField(default=None, null=True)
    source_forward_from_chat_id = BigIntegerField(default=None, null=True)
    source_forward_from_message_id = BigIntegerField(default=None, null=True)

    category = ForeignKeyField(
        Category,
        backref="history",
        on_delete="CASCADE",
    )
    category_message_id = BigIntegerField(default=None, null=True)
    category_media_group_id = CharField(default=None, null=True)
    category_message_rewritten = BooleanField(default=None, null=True)

    repeat_history = ForeignKeyField(
        "self",
        on_delete="SET NULL",
        null=True,
        default=None,
    )
    filter = ForeignKeyField(
        Filter,
        backref="history",
        on_delete="SET NULL",
        null=True,
        default=None,
    )

    created_at = DateTimeField(default=datetime.now)
    edited_at = DateTimeField(default=None, null=True)
    deleted_at = DateTimeField(default=None, null=True)

    data = BinaryJSONField()

    class Meta:
        table_name = "message_history"
