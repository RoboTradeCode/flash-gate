from enum import Enum, auto


# noinspection PyArgumentList
class StructureType(Enum):
    ORDER_BOOK = auto()
    PARTIAL_BALANCE = auto()
    ORDER = auto()
