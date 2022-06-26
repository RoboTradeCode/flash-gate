import json
import logging
from typing import Callable
from aeron import (
    Subscriber,
    Publisher,
    AeronPublicationAdminActionError,
    AeronPublicationNotConnectedError,
)


class Core:
    def __init__(self, config: dict, handler: Callable[[str], None]):
        aeron: dict = config["data"]["configs"]["gate_config"]["aeron"]
        subscribers: dict = aeron["subscribers"]
        publishers: dict = aeron["publishers"]

        self.logger = logging.getLogger(__name__)
        self.core = Subscriber(handler, **subscribers["core"])
        self.orderbooks = Publisher(**publishers["orderbooks"])
        self.balances = Publisher(**publishers["balances"])
        self.orders_statuses = Publisher(**publishers["core"])

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def poll(self):
        return self.core.poll()

    async def offer(self, event: dict):
        match event["action"]:
            case "order_book_update":
                publisher = self.orderbooks
            case "get_balance" | "balance_update":
                publisher = self.balances
            case "get_orders" | "orders_update":
                publisher = self.orders_statuses
            case _:
                return 0

        message = json.dumps("event")
        return await self._offer(publisher, message)

    async def _offer(self, publisher: Publisher, message: str):
        while True:
            try:
                publisher.offer(message)
                break
            except AeronPublicationNotConnectedError:
                break
            except AeronPublicationAdminActionError:
                msg = "Offer failed because of an administration action in the system"
                self.logger.warning(msg)

    async def close(self):
        self.core.close()
        self.orderbooks.close()
        self.balances.close()
        self.orders_statuses.close()
