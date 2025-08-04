from dataclasses import dataclass
from datetime import datetime, timedelta

import pytest
from peewee import (
    AutoField,
    DateTimeField,
    ForeignKeyField,
    IntegerField,
    Model,
    TextField,
)
from playhouse.sqlite_ext import JSONField, SqliteExtDatabase

import src.plugins.bot.utils.history_query as history_query


@dataclass
class Models:
    """Container for dynamically created peewee models used in tests."""

    db: SqliteExtDatabase
    Category: type[Model]
    Source: type[Model]
    MessageHistory: type[Model]


@pytest.fixture()
def models(monkeypatch) -> Models:
    """Create in-memory database and patch models in target module."""

    db = SqliteExtDatabase(":memory:")

    class BaseModel(Model):
        class Meta:
            database = db

    class Category(BaseModel):
        id = IntegerField(primary_key=True)
        title = TextField(null=True)

    class Source(BaseModel):
        id = IntegerField(primary_key=True)
        title = TextField(null=True)
        category = ForeignKeyField(Category, backref="sources")

    class MessageHistory(BaseModel):
        id = AutoField()
        source = ForeignKeyField(Source, backref="history")
        category = ForeignKeyField(Category, backref="history")
        category_message_id = IntegerField()
        created_at = DateTimeField()
        data = JSONField()

    db.create_tables([Category, Source, MessageHistory])

    monkeypatch.setattr(history_query, "Category", Category)
    monkeypatch.setattr(history_query, "Source", Source)
    monkeypatch.setattr(history_query, "MessageHistory", MessageHistory)
    monkeypatch.setattr(history_query, "get_message_link", lambda c, m: f"link-{c}-{m}")

    yield Models(db=db, Category=Category, Source=Source, MessageHistory=MessageHistory)

    db.drop_tables([Category, Source, MessageHistory])
    db.close()


@pytest.fixture
def now() -> datetime:
    return datetime(2023, 1, 1, 12, 0, 0)


@pytest.fixture
def freeze_now(monkeypatch, now) -> None:
    """Freeze ``datetime.now`` used in the module under test."""

    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return now

    monkeypatch.setattr(history_query, "datetime", FixedDatetime)


@pytest.fixture
def sample_history(models: Models, now: datetime):
    """Populate in-memory database with sample data for tests."""

    Category = models.Category
    Source = models.Source
    MessageHistory = models.MessageHistory

    cat1 = Category.create(id=1, title="c1")
    cat2 = Category.create(id=2, title="c2")
    src1 = Source.create(id=1, title="s1", category=cat1)
    src2 = Source.create(id=2, title="s2", category=cat2)

    MessageHistory.create(
        source=src1,
        category=cat1,
        category_message_id=101,
        created_at=now - timedelta(hours=1),
        data={"first_message": {"category": {"text": "text1"}}},
    )
    MessageHistory.create(
        source=src2,
        category=cat2,
        category_message_id=202,
        created_at=now - timedelta(hours=1),
        data={"last_message_without_error": {"category": {"caption": "cap2"}}},
    )
    MessageHistory.create(
        source=src1,
        category=cat1,
        category_message_id=303,
        created_at=now - timedelta(hours=5),
        data={"first_message": {"category": {"text": "old"}}},
    )


def test_get_history_messages_all(models, sample_history, freeze_now):
    result = history_query.get_history_messages(None, period_hours=2)

    assert result == [
        ("text1", "link-1-101"),
        ("cap2", "link-2-202"),
    ]


def test_get_history_messages_filtered(models, sample_history, freeze_now):
    result = history_query.get_history_messages(category_id=1, period_hours=2)

    assert result == [
        ("text1", "link-1-101"),
    ]
