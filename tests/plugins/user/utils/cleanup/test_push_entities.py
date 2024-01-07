from unittest.mock import Mock

import pytest

from plugins.user.utils.cleanup import push_entities


@pytest.mark.parametrize(
    [
        "offset",
        "length",
        "text_length",
        "input_entities",
        "exp_entities",
    ],
    [
        (
            0,
            0,
            2,
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=1, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=1, length=1),
            ],
        ),
        (
            2,
            3,
            4,
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=0, length=3),
                Mock(name="entity_4", offset=0, length=4),
                Mock(name="entity_5", offset=1, length=1),
                Mock(name="entity_6", offset=1, length=2),
                Mock(name="entity_7", offset=1, length=3),
                Mock(name="entity_8", offset=2, length=1),
                Mock(name="entity_9", offset=2, length=2),
                Mock(name="entity_10", offset=3, length=1),
            ],
            [
                Mock(name="entity_1", offset=0, length=1),
                Mock(name="entity_2", offset=0, length=2),
                Mock(name="entity_3", offset=0, length=6),
                Mock(name="entity_4", offset=0, length=7),
                Mock(name="entity_5", offset=1, length=1),
                Mock(name="entity_6", offset=1, length=5),
                Mock(name="entity_7", offset=1, length=6),
                Mock(name="entity_8", offset=5, length=1),
                Mock(name="entity_9", offset=5, length=2),
                Mock(name="entity_10", offset=6, length=1),
            ],
        ),
    ],
)
def test_push_entities_positive(
    offset: int,
    length: int,
    text_length: int,
    input_entities: list,
    exp_entities: list,
):
    act_entities = push_entities(
        entities=input_entities,
        offset=offset,
        length=length,
        text_length=text_length,
    )

    assert len(act_entities) == len(exp_entities)

    for idx in range(len(exp_entities)):
        act_entity = act_entities[idx]
        exp_entity = exp_entities[idx]

        assert act_entity._extract_mock_name() == exp_entity._extract_mock_name()
        assert act_entity.offset == exp_entity.offset
        assert act_entity.length == exp_entity.length
