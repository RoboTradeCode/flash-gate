import asyncio
import json
import logging
from aeron.concurrent import AsyncSleepingIdleStrategy
from .core import Core
from .enums import Event, Action
from .exchange import Exchange
from .formatters import Formatter
from .aliases import CreatingOrder


class Gate:
    def __init__(self, config: dict):
        assets: list = config["data"]["assets_labels"]
        markets: list = config["data"]["markets"]
        gate_config = config["data"]["configs"]["gate_config"]

        self.logger = logging.getLogger(__name__)
        self.exchange = Exchange(config)
        self.core = Core(config, self._event_handler)
        self.formatter = Formatter(config)
        self.idle_strategy = AsyncSleepingIdleStrategy(1)

        self.assets: list[str] = [asset["common"] for asset in assets]
        self.symbols: list[str] = [market["common_symbol"] for market in markets]
        self.depth: int = gate_config["info"]["depth"]
        self.ping_delay = gate_config["info"]["ping_delay"]
        self.subscribe_timeout = gate_config["rate_limits"]["subscribe_timeout"]

        self.data = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def run(self):
        tasks = [
            self._poll(),
            self._watch_order_books(),
            self._watch_balance(),
            self._watch_orders(),
            self._ping(),
        ]
        await asyncio.gather(*tasks)

    def _event_handler(self, message: str):
        try:
            event = json.loads(message)
            self.logger.info("Received message from Core: %s", event)

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

        except (json.JSONDecodeError, KeyError) as e:
            self.logger.error("Error in message parsing: %s", str(e))

    async def _create_orders(self, orders: list[CreatingOrder]):
        # [
        #     {
        #         "symbol": "XRP/USDT",
        #         "type": "market",
        #         "side": "sell",
        #         "amount": 64.212635,
        #         "price": 0.40221,
        #         "client_order_id": "9e743ffa-eb10-11ec-8fea-0242ac120002"
        #     }
        # ]
        orders = await self.exchange.create_orders(orders)
        message = await self.formatter.format(orders, Event.DATA, Action.CREATE_ORDERS)
        await self.core.offer(message)

    async def _cancel_orders(self, orders):
        # [
        #     {
        #         "client_order_id": "9e743ffa-eb10-11ec-8fea-0242ac120002",
        #         "symbol": "XRP/USDT"
        #     }
        # ]
        orders = await self.exchange.cancel_orders(orders)
        message = await self.formatter.format(orders, Event.DATA, Action.CANCEL_ORDERS)
        await self.core.offer(message)

    async def _cancel_all_orders(self):
        orders = await self.exchange.cancel_all_orders(self.symbols)
        action = Action.CANCEL_ALL_ORDERS
        message = await self.formatter.format(orders, Event.DATA, action)
        await self.core.offer(message)

    async def _get_orders(self, order):
        # [
        #     {
        #         "client_order_id": "9e743ffa-eb10-11ec-8fea-0242ac120002",
        #         "symbol": "XRP/USDT"
        #     }
        # ]
        order = await self.exchange.fetch_order(order)
        message = await self.formatter.format(order, Event.DATA, Action.GET_ORDERS)
        await self.core.offer(message)

    async def _get_balance(self, parts):
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
            message = self.formatter.format(self.data, Event.DATA, Action.PING)
            # TODO: Send to log server
            await asyncio.sleep(self.ping_delay)

    async def _poll(self):
        while True:
            fragments_read = await self.core.poll()
            await self.idle_strategy.idle(fragments_read)

    async def close(self):
        await self.exchange.close()
        await self.core.close()
