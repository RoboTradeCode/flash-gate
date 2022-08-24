from abc import ABC, abstractmethod
from .enum import EventAction
from .gate import Gate


class Command(ABC):
    @abstractmethod
    async def execute(self):
        ...


class CreateOrders(Command):
    def __init__(self, gate: Gate, event_id: str, action: EventAction):
        self.gate = gate

    async def execute(self):
        try:
            self.gate.no_priority_commands.clear()
            for param in event.get("data", []):
                if self.gate.sem.locked():
                    logger.info("Need more tokens!")

                async with self.gate.sem:
                    exchange = await self.get_exchange()
                    order = await exchange.create_order(param)

                order["client_order_id"] = param["client_order_id"]
                self.gate.event_id_by_client_order_id.set(
                    order["client_order_id"], event_id
                )
                self.gate.order_id_by_client_order_id.set(
                    order["client_order_id"], order["id"]
                )
                self.open_orders.add((order["client_order_id"], order["symbol"]))
        finally:
            self.no_priority_commands.set()


class CancelOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class CancelAllOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class GetOrders(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...


class GetBalance(Command):
    def __init__(self):
        ...

    async def execute(self):
        ...
