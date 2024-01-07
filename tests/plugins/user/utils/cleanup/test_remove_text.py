from unittest.mock import Mock

import pytest

from plugins.user.utils.cleanup import remove_text


@pytest.mark.parametrize(
    [
        "start",
        "end",
        "exp_next_offset",
        "input_text",
        "exp_text",
        "input_entities",
        "exp_entities",
    ],
    [
        # empty remove
        (
            0,
            0,
            0,
            "Текст",
            "Текст",
            [],
            [],
        ),
        # empty remove with entities
        (
            0,
            0,
            0,
            "Текст",
            "Текст",
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=5),
                Mock(name="entity_3", offset=1, length=3),
                Mock(name="entity_4", offset=4, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=5),
                Mock(name="entity_3", offset=1, length=3),
                Mock(name="entity_4", offset=4, length=1),
            ],
        ),
        # empty remove with entities & spaces
        (
            0,
            0,
            1,
            " Текст ",
            "Текст",
            [
                Mock(name="entity_to_be_deleted", offset=0, length=1),
                Mock(name="entity_1", offset=0, length=2),
                Mock(name="entity_2", offset=0, length=6),
                Mock(name="entity_3", offset=0, length=7),
                Mock(name="entity_4", offset=1, length=1),
                Mock(name="entity_5", offset=1, length=5),
                Mock(name="entity_6", offset=1, length=6),
                Mock(name="entity_7", offset=5, length=1),
                Mock(name="entity_8", offset=5, length=2),
                Mock(name="entity_to_be_deleted", offset=6, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=5),
                Mock(name="entity_3", offset=0, length=5),
                Mock(name="entity_4", offset=0, length=1),
                Mock(name="entity_5", offset=0, length=5),
                Mock(name="entity_6", offset=0, length=5),
                Mock(name="entity_7", offset=4, length=1),
                Mock(name="entity_8", offset=4, length=1),
            ],
        ),
        # remove all
        (
            0,
            5,
            5,
            "Текст",
            "",
            [
                Mock(name="entity_to_be_deleted", offset=0, length=1),
                Mock(name="entity_to_be_deleted", offset=0, length=5),
                Mock(name="entity_to_be_deleted", offset=1, length=3),
                Mock(name="entity_to_be_deleted", offset=4, length=1),
            ],
            [],
        ),
        # remove from beginning of text
        (
            0,
            2,
            2,
            "Текст",
            "кст",
            [
                Mock(name="entity_to_be_deleted", offset=0, length=1),
                Mock(name="entity_to_be_deleted", offset=0, length=2),
                Mock(name="entity_1", offset=0, length=5),
                Mock(name="entity_to_be_deleted", offset=1, length=1),
                Mock(name="entity_2", offset=1, length=2),
                Mock(name="entity_3", offset=2, length=1),
                Mock(name="entity_4", offset=3, length=1),
                Mock(name="entity_5", offset=4, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=3),
                Mock(name="entity_2", offset=0, length=1),
                Mock(name="entity_3", offset=0, length=1),
                Mock(name="entity_4", offset=1, length=1),
                Mock(name="entity_5", offset=2, length=1),
            ],
        ),
        # remove from middle of text
        (
            1,
            4,
            1,
            "Текст",
            "Т\n\nт",
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=0, length=4),
                Mock(name="entity_4", offset=0, length=5),
                Mock(name="entity_to_be_deleted", offset=1, length=1),
                Mock(name="entity_to_be_deleted", offset=1, length=3),
                Mock(name="entity_5", offset=1, length=4),
                Mock(name="entity_to_be_deleted", offset=3, length=1),
                Mock(name="entity_6", offset=3, length=2),
                Mock(name="entity_7", offset=4, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=1),
                Mock(name="entity_3", offset=0, length=1),
                Mock(name="entity_4", offset=0, length=4),
                Mock(name="entity_5", offset=3, length=1),
                Mock(name="entity_6", offset=3, length=1),
                Mock(name="entity_7", offset=3, length=1),
            ],
        ),
        # remove from middle of text with line break
        (
            3,
            6,
            3,
            "Т\n\nекст",
            "Т\n\nт",
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=0, length=4),
                Mock(name="entity_5", offset=0, length=7),
                Mock(name="entity_to_be_deleted", offset=1, length=1),
                Mock(name="entity_to_be_deleted", offset=1, length=5),
                Mock(name="entity_6", offset=1, length=6),
                Mock(name="entity_to_be_deleted", offset=5, length=1),
                Mock(name="entity_7", offset=5, length=2),
                Mock(name="entity_8", offset=6, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=1),
                Mock(name="entity_3", offset=0, length=1),
                Mock(name="entity_4", offset=0, length=1),
                Mock(name="entity_5", offset=0, length=4),
                Mock(name="entity_6", offset=3, length=1),
                Mock(name="entity_7", offset=3, length=1),
                Mock(name="entity_8", offset=3, length=1),
            ],
        ),
        # remove from end of text
        (
            3,
            5,
            2,
            "Текст",
            "Тек",
            [
                Mock(name="entity_1", offset=0, length=3),
                Mock(name="entity_2", offset=0, length=4),
                Mock(name="entity_3", offset=0, length=5),
                Mock(name="entity_4", offset=2, length=2),
                Mock(name="entity_to_be_deleted", offset=3, length=2),
                Mock(name="entity_to_be_deleted", offset=3, length=1),
                Mock(name="entity_to_be_deleted", offset=4, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=3),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=2, length=1),
            ],
        ),
        # remove from end of text with trailing space
        (
            3,
            5,
            3,
            "Текст ",
            "Тек",
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=4),
                Mock(name="entity_4", offset=0, length=6),
                Mock(name="entity_5", offset=2, length=2),
                Mock(name="entity_6", offset=2, length=4),
                Mock(name="entity_to_be_deleted", offset=3, length=1),
                Mock(name="entity_to_be_deleted", offset=3, length=2),
                Mock(name="entity_to_be_deleted", offset=3, length=3),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=0, length=3),
                Mock(name="entity_5", offset=2, length=1),
                Mock(name="entity_6", offset=2, length=1),
            ],
        ),
        # end with space
        (
            4,
            6,
            4,
            " Текст ",
            "Тек",
            [
                Mock(name="entity_to_be_deleted", offset=0, length=1),
                Mock(name="entity_1", offset=0, length=2),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=4),
                Mock(name="entity_4", offset=0, length=7),
                Mock(name="entity_5", offset=1, length=3),
                Mock(name="entity_6", offset=3, length=2),
                Mock(name="entity_7", offset=3, length=3),
                Mock(name="entity_to_be_deleted", offset=4, length=1),
                Mock(name="entity_to_be_deleted", offset=4, length=2),
                Mock(name="entity_to_be_deleted", offset=4, length=3),
                Mock(name="entity_to_be_deleted", offset=6, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=0, length=3),
                Mock(name="entity_5", offset=0, length=3),
                Mock(name="entity_6", offset=2, length=1),
                Mock(name="entity_7", offset=2, length=1),
            ],
        ),
        # end with line break
        (
            5,
            7,
            5,
            "Тек\n\nст ",
            "Тек",
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=4),
                Mock(name="entity_4", offset=0, length=8),
                Mock(name="entity_5", offset=1, length=1),
                Mock(name="entity_6", offset=1, length=2),
                Mock(name="entity_7", offset=1, length=3),
                Mock(name="entity_8", offset=1, length=4),
                Mock(name="entity_9", offset=2, length=1),
                Mock(name="entity_10", offset=2, length=2),
                Mock(name="entity_11", offset=2, length=3),
                Mock(name="entity_to_be_deleted", offset=3, length=1),
                Mock(name="entity_to_be_deleted", offset=3, length=2),
                Mock(name="entity_to_be_deleted", offset=3, length=5),
                Mock(name="entity_to_be_deleted", offset=7, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=3),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=0, length=3),
                Mock(name="entity_5", offset=1, length=1),
                Mock(name="entity_6", offset=1, length=2),
                Mock(name="entity_7", offset=1, length=2),
                Mock(name="entity_8", offset=1, length=2),
                Mock(name="entity_9", offset=2, length=1),
                Mock(name="entity_10", offset=2, length=1),
                Mock(name="entity_11", offset=2, length=1),
            ],
        ),
        #
        (
            3,
            5,
            1,
            "Текст 0",
            "Тек\n\n0",
            [
                Mock(name="entity_to_be_deleted", offset=3, length=3),
            ],
            [],
        ),
        (
            0,
            6,
            6,
            "to_del123\n\nТекст",
            "123\n\nТекст",
            [
                Mock(name="entity_1", offset=0, length=9),
            ],
            [
                Mock(name="entity_1", offset=0, length=3),
            ],
        ),
        (
            20,
            23,
            5,
            "НАСТОЯЩИЙ23\n\nТекст  | 1",
            "НАСТОЯЩИЙ23\n\nТекст",
            [
                Mock(name="entity_1", offset=0, length=11),
                Mock(name="entity_2", offset=13, length=7),
                Mock(name="entity_to_be_deleted", offset=22, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=11),
                Mock(name="entity_2", offset=13, length=5),
            ],
        ),
        (
            0,
            9,
            9,
            "НАСТОЯЩИЙ23\n\nТекст",
            "23\n\nТекст",
            [
                Mock(name="entity_1", offset=0, length=11),
                Mock(name="entity_2", offset=13, length=5),
            ],
            [
                Mock(name="entity_1", offset=0, length=2),
                Mock(name="entity_2", offset=4, length=5),
            ],
        ),
    ],
)
def test_remove_text_positive(
    start: int,
    end: int,
    exp_next_offset: int,
    input_text: str,
    exp_text: str,
    input_entities: list,
    exp_entities: list,
):
    act_text, act_entities, act_next_offset = remove_text(
        text=input_text,
        entities=input_entities,
        start=start,
        end=end,
    )

    assert act_text == exp_text

    assert len(act_entities) == len(exp_entities)

    for idx in range(len(exp_entities)):
        act_entity = act_entities[idx]
        exp_entity = exp_entities[idx]

        assert act_entity._extract_mock_name() == exp_entity._extract_mock_name()
        assert act_entity.offset == exp_entity.offset
        assert act_entity.length == exp_entity.length

    assert act_next_offset == exp_next_offset
