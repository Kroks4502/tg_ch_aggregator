from filter_types import FILTER_TYPES_BY_ID


def filter_type(filter_type_id: int):
    return "Тип", FILTER_TYPES_BY_ID.get(filter_type_id)


def pattern(value: str):
    return "Паттерн", f"`{value}`"
