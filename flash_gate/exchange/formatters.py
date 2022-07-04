from abc import ABC, abstractmethod
from .typing import OrderBook, Balance, Order
from .utils import filter_dict, get_timestamp_in_us


class Formatter(ABC):
    @abstractmethod
    def format(self, ccxt_structure: dict):
        pass


class OrderBookFormatter(Formatter):
    KEYS = ["symbol", "bids", "asks", "timestamp"]

    def format(self, ccxt_structure: dict) -> OrderBook:
        order_book = filter_dict(ccxt_structure, self.KEYS)
        order_book["timestamp"] = get_timestamp_in_us(ccxt_structure)
        return order_book


class BalanceFormatter(Formatter):
    KEYS = ["assets", "timestamp"]

    def format(self, ccxt_structure: dict) -> Balance:
        balance = filter_dict(ccxt_structure, self.KEYS)
        balance["timestamp"] = get_timestamp_in_us(ccxt_structure)
        return balance


class OrderFormatter(Formatter):
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

    def format(self, ccxt_structure: dict) -> Order:
        order = filter_dict(ccxt_structure, self.KEYS)
        order["timestamp"] = get_timestamp_in_us(ccxt_structure)
        return order


class FormatterFactory(ABC):
    @abstractmethod
    def make_formatter(self, ccxt_structure: dict) -> Formatter:
        pass


class FormatterFactoryImpl(FormatterFactory):
    def make_formatter(self, ccxt_structure: dict) -> Formatter:
        if "bids" in ccxt_structure:
            return OrderBookFormatter()
        if "total" in ccxt_structure:
            return BalanceFormatter()
        if "id" in ccxt_structure:
            return OrderFormatter()
        raise TypeError()
