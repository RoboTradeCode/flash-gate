from flash_gate.types import OrderBook
from abc import ABC, abstractmethod


class Formatter(ABC):
    @abstractmethod
    def format(self, data):
        pass


class OrderBookFormatter(Formatter):
    KEYS = ["symbol", "bids", "asks", "timestamp"]

    def format(self, data: dict):
        filtered = self
