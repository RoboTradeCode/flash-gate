import asyncio
import json
import logging
import uuid
from typing import NoReturn, Coroutine
from bidict import bidict
from .connector import AeronConnector
from .enums import EventAction
from .exchange import CcxtExchange
from .exchange.types import FetchOrderParams, CreateOrderParams
from .types import Event

PING_DELAY_IN_SECONDS = 1


class Gate:
    def __init__(self, config: dict):
        gate_config = config["data"]["configs"]["gate_config"]
        exchange_id = gate_config["exchange"]["exchange_id"]
        exchange_config = self._get_exchange_config(gate_config)

        self.logger = logging.getLogger(__name__)
        self.exchange = CcxtExchange(exchange_id, exchange_config)
        self.connector = AeronConnector(config, self._handler)

        self.assets = self._get_assets(config["data"]["assets_labels"])
        self.symbols = self._get_symbols(config["data"]["markets"])
        self.depth: int = gate_config["gate"]["order_book_depth"]
        self.data_collection_method = gate_config["data_collection_method"]

        self.event_id_by_client_order_id = bidict()
        self.order_books_received = 0

    @staticmethod
    def _get_exchange_config(gate_config: dict) -> dict:
        return {
            "apiKey": gate_config["exchange"]["credentials"]["api_key"],
            "secret": gate_config["exchange"]["credentials"]["secret_key"],
            "password": gate_config["exchange"]["credentials"]["password"],
            "enableRateLimit": gate_config["rate_limits"]["enable_ccxt_rate_limiter"],
        }

    @staticmethod
    def _get_assets(assets_labels: list) -> list[str]:
        return [asset_label["common"] for asset_label in assets_labels]

    @staticmethod
    def _get_symbols(markets: list) -> list[str]:
        return [market["common_symbol"] for market in markets]

    async def run(self) -> NoReturn:
        tasks = self._get_background_tasks()
        await asyncio.gather(*tasks)

    def _get_background_tasks(self) -> list[Coroutine]:
        return [
            self.connector.run(),
            self._watch_order_books(),
            self._watch_balance(),
            self._watch_orders(),
            self._health_check(),
        ]

    def _handler(self, message: str) -> None:
        self.logger.info("Received message: %s", message)
        event = self._deserialize_message(message)
        task = self._get_task(event)
        asyncio.create_task(task)

    def _deserialize_message(self, message: str) -> Event:
        try:
            event = json.loads(message)
            self.connector.offer(event, only_log=True)
            return event
        except json.JSONDecodeError as e:
            self.logger.error("Message deserialize error: %s", e)

    def _get_task(self, event: Event) -> Coroutine:
        if not isinstance(event, dict):
            return asyncio.sleep(0)

        # TODO: Создавать полиморфные классы
        match event.get("action"):
            case EventAction.CREATE_ORDERS:
                return self._create_orders(event)
            case EventAction.CANCEL_ORDERS:
                return self._cancel_orders(event)
            case EventAction.CANCEL_ALL_ORDERS:
                return self._cancel_all_orders()
            case EventAction.GET_ORDERS:
                return self._get_orders(event)
            case EventAction.GET_BALANCE:
                return self._get_balance(event)
            case _:
                logging.warning("Unknown action: %s", event["action"])
                return asyncio.sleep(0)

    async def _create_orders(self, event: Event):
        event_id = event["event_id"]
        orders: list[CreateOrderParams] = event["data"]

        self._associate_with_event(event_id, orders)
        orders = await self.exchange.create_orders(orders)

        event: Event = {
            "event_id": event_id,
            "action": EventAction.CREATE_ORDERS,
            "data": orders,
        }
        self.connector.offer(event)

    def _associate_with_event(
        self, event_id: str, orders: list[CreateOrderParams]
    ) -> None:
        client_order_ids = self._get_client_order_ids(orders)
        for client_order_id in client_order_ids:
            self.event_id_by_client_order_id[client_order_id] = event_id

    @staticmethod
    def _get_client_order_ids(orders: list[CreateOrderParams]) -> list[str]:
        return [order["client_order_id"] for order in orders]

    async def _cancel_orders(self, event: Event) -> None:
        orders: list[FetchOrderParams] = event["data"]
        await self.exchange.cancel_orders(orders)

    async def _cancel_all_orders(self) -> None:
        await self.exchange.cancel_all_orders(self.symbols)

    async def _get_orders(self, event: Event) -> None:
        orders: list[FetchOrderParams] = event["data"]
        for order in orders:
            await self._get_order(order)

    async def _get_order(self, order: FetchOrderParams):
        order = await self.exchange.fetch_order(order)

        event: Event = {
            "event_id": self.event_id_by_client_order_id.get(order["client_order_id"]),
            "action": EventAction.GET_ORDERS,
            "data": [order],
        }
        self.connector.offer(event)

    async def _get_balance(self, event: Event) -> None:
        if not (assets := event["data"]):
            assets = self.assets

        balance = await self.exchange.fetch_partial_balance(assets)

        event: Event = {
            "event_id": event["event_id"],
            "action": EventAction.GET_BALANCE,
            "data": balance,
        }
        self.connector.offer(event)

    async def _watch_order_books(self):
        tasks = [self._watch_order_book(symbol, self.depth) for symbol in self.symbols]
        await asyncio.gather(*tasks)

    async def _watch_order_book(self, symbol, limit):
        while True:

            if self.data_collection_method["order_book"] == "websocket":
                order_book = await self.exchange.watch_order_book(symbol, limit)
            else:
                order_book = await self.exchange.fetch_order_book(symbol, limit)

            self.order_books_received += 1
            event: Event = {
                "event_id": str(uuid.uuid4()),
                "action": EventAction.ORDER_BOOK_UPDATE,
                "data": order_book,
            }
            self.connector.offer(event, log=False)

    async def _watch_balance(self) -> None:
        while True:

            if self.data_collection_method["balance"] == "websocket":
                balance = await self.exchange.watch_partial_balance(self.assets)
            else:
                balance = await self.exchange.fetch_partial_balance(self.assets)

            event: Event = {
                "event_id": str(uuid.uuid4()),
                "action": EventAction.BALANCE_UPDATE,
                "data": balance,
            }
            self.connector.offer(event)

    async def _watch_orders(self) -> None:
        while True:

            try:
                if self.data_collection_method["order"] == "websocket":
                    orders = await self.exchange.watch_orders()
                else:
                    orders = await self.exchange.fetch_open_orders(self.symbols)

                for order in orders:
                    event: Event = {
                        "event_id": self.event_id_by_client_order_id.get(
                            order["client_order_id"]
                        ),
                        "action": EventAction.ORDERS_UPDATE,
                        "data": order,
                    }
                    self.connector.offer(event)
            except Exception as e:
                self.logger.error(e)

    async def _health_check(self) -> NoReturn:
        while True:
            self._ping()
            await asyncio.sleep(PING_DELAY_IN_SECONDS)

    def _ping(self):
        event: Event = {
            "event_id": str(uuid.uuid4()),
            "action": EventAction.PING,
            "data": self.order_books_received,
        }
        self.connector.offer(event, log=False)

    async def close(self):
        await self.exchange.close()
        await self.connector.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
