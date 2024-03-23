from enum import Enum


class Operation(Enum):
    NEW = "отправил"
    NEW_GROUP = "отправил группу"
    EDIT = "изменил"
    DELETE = "удалил"
