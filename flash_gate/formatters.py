import json
from datetime import datetime
from .enums import Event, Node, Action


class Formatter:
    def __init__(self, algo: str, node: Node, exchange: str, instance: str):
        self.exchange = exchange
        self.node = node
        self.instance = instance
        self.algo = algo

    def format(self, event_id: str, event: Event, action: Action, data) -> str:
        deserialized_message = {
            "event_id": event_id,
            "event": event,
            "exchange": self.exchange,
            "node": self.node,
            "instance": self.instance,
            "algo": self.algo,
            "action": action,
            "message": "",
            "timestamp": self._get_timestamp_in_us(),
            "data": data,
        }

        message = json.dumps(deserialized_message)
        return message

    @staticmethod
    def _get_timestamp_in_us() -> int:
        return int(datetime.now().timestamp() * 1000000)
