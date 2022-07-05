from abc import ABC, abstractmethod
from .types import OrderBook, Balance, Order
from .enums import StructureType
from .utils import filter_dict, get_timestamp_in_us


class Formatter(ABC):
    @abstractmethod
    def format(self, structure: dict):
        pass


class CcxtOrderBookFormatter(Formatter):
    KEYS = ["symbol", "bids", "asks", "timestamp"]

    def format(self, structure: dict) -> OrderBook:
        order_book = filter_dict(structure, self.KEYS)
        order_book["timestamp"] = get_timestamp_in_us(structure)
        return order_book


class CcxtBalanceFormatter(Formatter):
    KEYS = ["assets", "timestamp"]

    def format(self, structure: dict) -> Balance:
        balance = filter_dict(structure, self.KEYS)
        balance["timestamp"] = get_timestamp_in_us(structure)
        return balance


class CcxtOrderFormatter(Formatter):
    KEYS = [
        "client_order_id",
        "symbol",
        "type",
        "side",
        "amount",
        "price",
        "id",
        "status",
        "filled",
        "timestamp",
    ]

    def format(self, structure: dict) -> Order:
        order = filter_dict(structure, self.KEYS)
        order["timestamp"] = get_timestamp_in_us(structure)
        return order


class FormatterFactory(ABC):
    @abstractmethod
    def make_formatter(self, structure_type: StructureType) -> Formatter:
        pass


class CcxtFormatterFactory(FormatterFactory):
    def make_formatter(self, structure_type: StructureType) -> Formatter:
        match structure_type:
            case StructureType.ORDER_BOOK:
                return CcxtOrderBookFormatter()
            case StructureType.BALANCE:
                return CcxtBalanceFormatter()
            case StructureType.ORDER:
                return CcxtOrderFormatter()
            case _:
                raise TypeError()
