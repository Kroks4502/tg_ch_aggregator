from copy import deepcopy
from unittest.mock import Mock

from plugins.user.utils.cleanup import remove_text


def test_remove_text_empty_cut():
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="Текст",
        entities=[
            Mock(offset=0, length=5),
        ],
    )
    msg = deepcopy(exp_msg)
    offset = remove_text(msg, start=0, end=0, is_media=False)

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 0


def test_remove_text_start():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="Текст",
        entities=[
            Mock(name="entity_1", offset=0, length=5),
            Mock(name="entity_2", offset=2, length=1),
            Mock(name="entity_3", offset=0, length=2),
        ],
    )
    offset = remove_text(msg, start=0, end=2, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="кст",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=3),
            Mock(name="exp_entity_2", offset=0, length=1),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 2


def test_remove_text_middle():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="Текст",
        entities=[
            Mock(name="entity_1", offset=0, length=5),
            Mock(name="entity_2", offset=4, length=1),
            Mock(name="entity_3", offset=1, length=3),
        ],
    )
    offset = remove_text(msg, start=1, end=4, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="Т\n\nт",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=4),
            Mock(name="exp_entity_2", offset=3, length=1),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 1


def test_remove_text_middle_with_line_break():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="Т\n\nекст",
        entities=[
            Mock(name="entity_1", offset=0, length=5),
            Mock(name="entity_2", offset=0, length=7),
            Mock(name="entity_3", offset=3, length=3),
        ],
    )
    offset = remove_text(msg, start=3, end=6, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="Т\n\nт",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=1),
            Mock(name="exp_entity_2", offset=0, length=4),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 3


def test_remove_text_end():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="Текст ",
        entities=[
            Mock(name="entity_1", offset=0, length=6),
            Mock(name="entity_2", offset=0, length=3),
            Mock(name="entity_3", offset=3, length=2),
        ],
    )
    offset = remove_text(msg, start=3, end=5, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="Тек",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=3),
            Mock(name="exp_entity_2", offset=0, length=3),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 3


def test_remove_text_end_2():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="Текст 0",
        entities=[
            Mock(name="entity_1", offset=3, length=3),
        ],
    )
    offset = remove_text(msg, start=3, end=5, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="Тек\n\n0",
        entities=[],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 1


def test_remove_text_end_3():
    """на `=` в `if start <= n < end` >> src/plugins/user/utils/cleanup.py:78"""
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="2\n\nТекст | 1",
        entities=[
            Mock(name="entity_1", offset=0 + 3, length=6),
            Mock(name="entity_2", offset=8 + 3, length=1),
            Mock(name="entity_3", offset=11, length=1),
        ],
    )
    offset = remove_text(msg, start=5 + 3 + 1, end=9 + 3, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="2\n\nТекст",
        entities=[
            Mock(name="exp_entity_1", offset=0 + 3, length=5),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 4


def test_remove_text_1():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="to_del123\n\nТекст",
        entities=[
            Mock(name="entity_1", offset=0, length=9),
        ],
    )
    offset = remove_text(msg, start=0, end=6, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="123\n\nТекст",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=3),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 6


# ---------
def test_remove_text_2():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="НАСТОЯЩИЙ23\n\nТекст  | 1",
        entities=[
            Mock(name="entity_1", offset=0, length=11),
            Mock(name="entity_2", offset=13, length=7),
            Mock(name="entity_3", offset=22, length=1),
        ],
    )
    offset = remove_text(msg, start=20, end=23, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="НАСТОЯЩИЙ23\n\nТекст",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=11),
            Mock(name="exp_entity_2", offset=13, length=5),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 5


def test_remove_text_3():
    msg = Mock(
        caption=None,
        caption_entities=None,
        text="НАСТОЯЩИЙ23\n\nТекст",
        entities=[
            Mock(name="entity_1", offset=0, length=11),
            Mock(name="entity_2", offset=13, length=5),
        ],
    )
    offset = remove_text(msg, start=0, end=9, is_media=False)
    exp_msg = Mock(
        caption=None,
        caption_entities=None,
        text="23\n\nТекст",
        entities=[
            Mock(name="exp_entity_1", offset=0, length=2),
            Mock(name="exp_entity_2", offset=13 - 9, length=5),
        ],
    )

    assert msg.text == exp_msg.text

    assert len(msg.entities) == len(exp_msg.entities)
    for idx in range(len(exp_msg.entities)):
        assert msg.entities[idx].offset == exp_msg.entities[idx].offset
        assert msg.entities[idx].length == exp_msg.entities[idx].length

    assert offset == 9
