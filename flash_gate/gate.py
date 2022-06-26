import asyncio
import json
import logging
from aeron.concurrent import AsyncSleepingIdleStrategy
from flash_gate.exchange import Exchange
from .formatters import Formatter
from .core import Core
from .enums import Event, Action


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

            # TODO: Log Server
            # log_message = dict(message)
            # log_message["node"] = "gate"
            # self.logger.info(json.dumps(log_message))

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
            self.logger.error("Error in event parsing: %s", str(e))

    async def _create_orders(self, orders):
        orders = await self.exchange.create_orders(orders)
        logging.info("Received orders from exchange: %s", orders)

        for order in orders:
            match order["status"]:
                case "open":
                    action = "order_created"
                case "closed":
                    action = "order_closed"
                case _:
                    action = "order_status"

            message = self.formatter.format(order, action)
            logging.info("Sending order to core: %s", message)
            self.logger.info(json.dumps(message))

            self.core.offer(message)

    async def _cancel_orders(self, orders):
        orders = await self.exchange.cancel_orders(orders)
        logging.info("Received orders from exchange: %s", orders)

        for order in orders:
            match order["status"]:
                case "open":
                    action = "order_created"
                case "closed":
                    action = "order_closed"
                case _:
                    action = "order_status"

            message = self.formatter.format(order, action)
            logging.info("Sending order to core: %s", message)
            self.logger.info(json.dumps(message))

            self.core.offer(message)

    async def _cancel_all_orders(self):
        orders = await self.exchange.cancel_all_orders()
        logging.info("Received orders from exchange: %s", orders)

        for order in orders:
            match order["status"]:
                case "open":
                    action = "order_created"
                case "closed":
                    action = "order_closed"
                case _:
                    action = "order_status"

            message = self.formatter.format(order, action)
            logging.info("Sending order to core: %s", message)
            self.logger.info(json.dumps(message))

            self.core.offer(message)

    async def _order_status(self, order):
        order = await self.exchange.get_order(order)
        logging.info("Received order from exchange: %s", order)

        message = self.formatter.format(order, "order_status")
        logging.info("Sending order status to core: %s", message)
        self.logger.info(json.dumps(message))

        self.core.offer(message)

    async def _get_balances(self, parts):
        balance = await self.exchange.get_balance()
        default_balance = {"free": 0.0, "used": 0.0, "total": 0.0}
        balance = {part: balance.get(part, default_balance) for part in parts}
        logging.info("Received balance from exchange: %s", balance)

        message = self.formatter.format(balance, "balances")
        logging.info("Sending balance to core: %s", message)
        self.logger.info(json.dumps(message))

        self.core.offer(message)

    async def _watch_order_book(self, symbol, limit):
        await asyncio.sleep(self.subscribe_timeout)
        while True:
            orderbook = await self.exchange.get_order_book(symbol, limit)
            self.data += 1

            message = self.formatter.format(orderbook, "orderbook", symbol)
            self.core.offer(message)

    async def _watch_order_books(self):
        tasks = [self._watch_order_book(symbol, self.depth) for symbol in self.symbols]
        await asyncio.gather(*tasks)

    async def _watch_balance(self) -> None:
        while True:
            balance = await self.exchange.get_balance()
            default_balance = {"free": 0.0, "used": 0.0, "total": 0.0}
            balance = {part: balance.get(part, default_balance) for part in self.assets}
            logging.info("Received balance from exchange: %s", balance)

            message = self.formatter.format(balance, "balances")
            logging.info("Sending balance to core: %s", message)
            self.logger.info(json.dumps(message))

            self.core.offer(message)

    async def _watch_orders(self) -> None:
        while True:
            orders = await self.exchange.get_orders()
            logging.info("Received orders from exchange: %s", orders)

            for order in orders:
                match order["status"]:
                    case "open":
                        action = "order_created"
                    case "closed":
                        action = "order_closed"
                    case _:
                        action = "order_status"

                message = self.formatter.format(order, action)
                logging.info("Sending order to core: %s", message)
                self.logger.info(json.dumps(message))

                self.core.offer(message)

    async def _ping(self):
        while True:
            message = self.formatter.format(self.data, "ping")
            self.logger.info(json.dumps(message))
            await asyncio.sleep(self.ping_delay)

    async def _poll(self):
        while True:
            fragments_read = await self.core.poll()
            await self.idle_strategy.idle(fragments_read)

    async def close(self):
        await self.exchange.close()
        self.core.close()
