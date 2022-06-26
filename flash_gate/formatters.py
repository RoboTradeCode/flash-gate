import uuid
from datetime import datetime
from .enums import Event, Node, Action


class Formatter:
    def __init__(self, config: dict):
        info = config["data"]["configs"]["gate_config"]["info"]

        self.algo: str = config["algo"]
        self.node: Node = info["node"]
        self.exchange: str = info["exchange"]
        self.instance: str = info["instance"]

    async def format(self, data, event: Event, action: Action, message: str = ""):
        formatted = await self._template
        formatted["event"] = event
        formatted["action"] = action
        formatted["message"] = message

        # Форматирование данных
        match action:
            case Action.ORDER_BOOK_UPDATE:
                formatted["data"] = self._format_order_book(data)
            case Action.GET_BALANCE | Action.BALANCE_UPDATE:
                formatted["data"] = self._format_balance(data)
            case Action.CREATE_ORDERS | Action.GET_ORDERS | Action.ORDERS_UPDATE:
                formatted["data"] = self._format_orders(data)

        return formatted

    @property
    async def _template(self):
        return {
            "event_id": uuid.uuid1(),
            "node": self.node,
            "exchange": self.exchange,
            "instance": self.instance,
            "algo": self.algo,
            "timestamp": int(datetime.now().timestamp() * 1000000),
        }

    @staticmethod
    async def _format_order_book(data: dict):
        keys = ["bids", "asks", "symbol", "timestamp"]
        return {key: data[key] for key in data if key in keys}

    @staticmethod
    async def _format_balance(data):
        return data

    @staticmethod
    async def _format_orders(data: dict):
        return [Formatter._format_order(order) for order in data]

    @staticmethod
    async def _format_order(order: dict):
        keys = [
            "id",
            "timestamp",
            "status",
            "symbol",
            "type",
            "side",
            "price",
            "amount",
            "filled",
        ]
        return {key: order[key] for key in order if key in keys}
