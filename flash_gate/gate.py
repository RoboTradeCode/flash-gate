import asyncio
import json
import logging
from aeron.concurrent import AsyncSleepingIdleStrategy
from .core import Core
from .enums import Event, Action
from .exchange import Exchange
from .formatters import Formatter
from .types import CreateOrderData, FetchOrderData
from typing import NoReturn, Coroutine

class Gate:
    def __init__(self, config: dict):
        gate_config = config["data"]["configs"]["gate_config"]

        self.logger = logging.getLogger(__name__)
        self.exchange = Exchange("kuna", self._get_exchange_config(gate_config))
        self.core = Core(config, self._message_handler)
        self.formatter = Formatter()
        self.idle_strategy = AsyncSleepingIdleStrategy(1)

        self.assets = self._get_assets(config["data"]["assets_labels"])
        self.symbols = self._get_symbols(config["data"]["markets"])
        self.depth: int = gate_config["info"]["depth"]
        self.ping_delay: float = gate_config["info"]["ping_delay"]
        self.subscribe_timeout: float = gate_config["rate_limits"]["subscribe_timeout"]

        self.data = 0

    @staticmethod
    def _get_exchange_config(gate_config: dict) -> dict:
        return {
            "apiKey": gate_config["account"]["api_key"],
            "secret": gate_config["account"]["secret_key"],
            "password": gate_config["account"]["password"],
            "enableRateLimit": gate_config["rate_limits"]["enable_ccxt_rate_limiter"],
        }

    @staticmethod
    def _get_assets(assets_labels: list) -> list[str]:
        return [asset_label["common"] for asset_label in assets_labels]

    @staticmethod
    def _get_symbols(markets: list) -> list[str]:
        return [market["common_symbol"] for market in markets]

    async def run(self) -> NoReturn:
        tasks = self._get_tasks()
        await asyncio.gather(*tasks)

    def _get_tasks(self) -> list:
        return [
            self._poll(),
            self._watch_order_books(),
            self._watch_balance(),
            self._watch_orders(),
            self._ping(),
        ]

    def _message_handler(self, message: str):
        self.logger.info("Received message: %s", message)
        event = self._deserialize_message(message)

        match event["event"], event["action"]:
            case Event.COMMAND, Action.CREATE_ORDERS:
                asyncio.create_task(self._create_orders(event["data"]))
            case Event.COMMAND, Action.CANCEL_ORDERS:
                asyncio.create_task(self._cancel_orders(event["data"]))
            case Event.COMMAND, Action.CANCEL_ALL_ORDERS:
                asyncio.create_task(self._cancel_all_orders())
            case Event.COMMAND, Action.GET_ORDERS:
                asyncio.create_task(self._get_orders(event["data"]))
            case Event.COMMAND, Action.GET_BALANCE:
                asyncio.create_task(self._get_balance(event["data"]))
            case _:
                logging.warning("Unknown event type: %s", event)

    def _deserialize_message(self, message: str) -> dict:
        try:
            return json.loads(message)
        except json.JSONDecodeError as e:
            self.logger.error("Message deserialize error: %s", e)

    def _get_task(self, action: Action) -> Coroutine:


    async def _create_orders(self, orders: list[CreateOrderData]):
        orders = await self.exchange.create_orders(orders)
        message = self.formatter.format(orders, Event.DATA, Action.CREATE_ORDERS)
        await self.core.offer(message)

    async def _cancel_orders(self, orders: list[FetchOrderData]):
        orders = await self.exchange.cancel_orders(orders)
        message = await self.formatter.format(orders, Event.DATA, Action.CANCEL_ORDERS)
        await self.core.offer(message)

    async def _cancel_all_orders(self):
        orders = await self.exchange.cancel_all_orders(self.symbols)
        action = Action.CANCEL_ALL_ORDERS
        message = await self.formatter.format(orders, Event.DATA, action)
        await self.core.offer(message)

    async def _get_orders(self, orders: list[FetchOrderData]):
        # [
        #     {
        #         "client_order_id": "9e743ffa-eb10-11ec-8fea-0242ac120002",
        #         "symbol": "XRP/USDT"
        #     }
        # ]
        tasks = [self._get_order(order) for order in orders]
        await asyncio.gather(*tasks)

    async def _get_order(self, order: FetchOrderData):
        # {
        #     "client_order_id": "9e743ffa-eb10-11ec-8fea-0242ac120002",
        #     "symbol": "XRP/USDT"
        # }
        order = await self.exchange.fetch_order(order)
        message = await self.formatter.format(order, Event.DATA, Action.GET_ORDERS)
        await self.core.offer(message)

    async def _get_balance(self, parts: list[str]):
        # [
        #     "BTC",
        #     "ETH",
        #     "USDT"
        # ]
        #
        # [
        #
        # ]
        balance = await self.exchange.fetch_balance()

        if parts:
            default_balance = {"free": 0.0, "used": 0.0, "total": 0.0}
            balance = {part: balance.get(part, default_balance) for part in parts}

        message = await self.formatter.format(balance, Event.DATA, Action.GET_BALANCE)
        await self.core.offer(message)

    async def _watch_order_books(self):
        tasks = [self._watch_order_book(symbol, self.depth) for symbol in self.symbols]
        await asyncio.gather(*tasks)

    async def _watch_order_book(self, symbol, limit):
        await asyncio.sleep(self.subscribe_timeout)
        event = Event.DATA
        action = Action.ORDER_BOOK_UPDATE

        while True:
            orderbook = await self.exchange.watch_order_book(symbol, limit)
            self.data += 1
            message = await self.formatter.format(orderbook, event, action)
            await self.core.offer(message)

    async def _watch_balance(self) -> None:
        await asyncio.sleep(self.subscribe_timeout)
        event = Event.DATA
        action = Action.GET_BALANCE

        while True:
            balance = await self.exchange.watch_balance()
            default_balance = {"free": 0.0, "used": 0.0, "total": 0.0}
            balance = {part: balance.get(part, default_balance) for part in self.assets}
            message = await self.formatter.format(balance, event, action)
            await self.core.offer(message)

    async def _watch_orders(self) -> None:
        await asyncio.sleep(self.subscribe_timeout)
        event = Event.DATA
        action = Action.ORDERS_UPDATE

        while True:
            orders = await self.exchange.watch_orders()
            for order in orders:
                message = await self.formatter.format(order, event, action)
                await self.core.offer(message)

    async def _ping(self):
        while True:
            # TODO: Send to log server
            message = await self.formatter.format(self.data, Event.DATA, Action.PING)
            await asyncio.sleep(self.ping_delay)

    async def _poll(self):
        while True:
            fragments_read = await self.core.poll()
            await self.idle_strategy.idle(fragments_read)

    async def close(self):
        await self.exchange.close()
        await self.core.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
