import json
from datetime import datetime
from .enums import Node
from .types import Message


class Formatter:
    def __init__(self, algo: str, node: Node, exchange: str, instance: str):
        self.exchange = exchange
        self.node = node
        self.instance = instance
        self.algo = algo

    def format(self, message: Message) -> str:
        template = self._get_template()
        filled = self._fill_template(template, message)
        return self._serialize(filled)

    def _get_template(self) -> dict:
        return {
            "event_id": None,
            "event": None,
            "exchange": self.exchange,
            "node": self.node,
            "instance": self.instance,
            "algo": self.algo,
            "action": None,
            "message": "",
            "timestamp": self._get_timestamp_in_us(),
            "data": None,
        }

    @staticmethod
    def _get_timestamp_in_us() -> int:
        return int(datetime.now().timestamp() * 1_000_000)

    @staticmethod
    def _fill_template(template: dict, data: dict) -> dict:
        filled = template.copy()
        for key, value in data.items():
            filled[key] = value
        return filled

    @staticmethod
    def _serialize(message: dict) -> str:
        return json.dumps(message)
