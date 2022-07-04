from abc import ABC, abstractmethod
from flash_gate.typing import Event, OrderBook, Order


class Formatter(ABC):
    @abstractmethod
    def format(self, event: Event, data):
        pass


class OrderBookFormatter(Formatter):
    KEYS = ["symbol", "bids", "asks", "timestamp"]

    def format(self, event: Event, data: dict) -> OrderBook:
        ...


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

    def format(self, event: Event, data: dict) -> Order:
        ...
