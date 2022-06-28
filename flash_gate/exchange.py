import asyncio
import itertools
import ccxtpro
from bidict import bidict
from ccxtpro import Exchange as BaseExchange
from .types import FetchOrderData, CreateOrderData, OrderBook, Balance, Order


class Exchange:
    def __init__(self, exchange_id: str, config: dict):
        self.exchange: BaseExchange = getattr(ccxtpro, exchange_id)(config)
        self.orders = bidict()  # id by client_order_id

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_order_book(self, symbol: str, limit: int) -> OrderBook:
        orderbook = await self.exchange.fetch_order_book(symbol, limit)
        orderbook["timestamp"] *= 1000  # ms to us
        return orderbook

    async def watch_order_book(self, symbol: str, limit: int) -> OrderBook:
        if self.exchange.has.get("watchOrderBook"):
            return await self.exchange.watch_order_book(symbol, limit)
        return await self.fetch_order_book(symbol, limit)

    async def fetch_balance(self, parts: list[str]) -> Balance:
        balance = await self.exchange.fetch_balance()
        return self._get_partial_balance(balance, parts)

    @staticmethod
    def _get_partial_balance(balance, parts: list[str]):
        default = {"free": 0.0, "used": 0.0, "total": 0.0}
        partial_balance = {part: balance.get(part, default) for part in parts}
        partial_balance["timestamp"] = balance.get("timestamp")
        return partial_balance

    async def watch_balance(self, parts: list[str]) -> Balance:
        if self.exchange.has.get("watchBalance"):
            balance = await self.exchange.watch_balance()
            return self._get_partial_balance(balance, parts)
        return await self.fetch_balance(parts)

    async def fetch_order(self, data: FetchOrderData) -> Order:
        order_id = self.orders[data["client_order_id"]]
        order = await self.exchange.fetch_order(order_id, data["symbol"])
        order["client_order_id"] = data["client_order_id"]
        return order

    async def watch_orders(self) -> list[Order]:
        orders = await self.exchange.watch_orders()
        for order in orders:
            order["client_order_id"] = self.orders.inverse[order["id"]]
        return orders

    async def create_orders(self, orders: list[CreateOrderData]) -> list[Order]:
        tasks = [self._create_order(order) for order in orders]
        # noinspection PyTypeChecker
        return await asyncio.gather(*tasks)

    async def _create_order(self, data: CreateOrderData) -> Order:
        order = await self.exchange.create_order(
            data["symbol"],
            data["type"],
            data["side"],
            data["amount"],
            data["price"],
        )
        self.orders[data["client_order_id"]] = order["id"]
        return self._populate_order(order, data)

    @staticmethod
    def _populate_order(order, data: CreateOrderData):
        order["client_order_id"] = data["client_order_id"]
        for key in data:
            if order[key] is None:
                # noinspection PyTypedDict
                order[key] = data[key]
        return order

    async def cancel_orders(self, orders: list[FetchOrderData]):
        tasks = [self._cancel_order(order) for order in orders]
        await asyncio.gather(*tasks)

    async def _cancel_order(self, order: FetchOrderData):
        order_id = self.orders[order["client_order_id"]]
        await self.exchange.cancel_order(order_id, order["symbol"])

    async def cancel_all_orders(self, symbols: list[str]):
        orders = await self._fetch_open_orders(symbols)
        await self.cancel_orders(orders)

    async def _fetch_open_orders(self, symbols: list[str]):
        tasks = [self.exchange.fetch_open_orders(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return list(itertools.chain.from_iterable(results))

    async def close(self):
        await self.exchange.close()
