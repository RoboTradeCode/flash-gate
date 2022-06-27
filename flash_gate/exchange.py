import asyncio
import itertools
import ccxtpro
from ccxtpro import Exchange as BaseExchange
from bidict import bidict
from .types import FetchOrderData, CreateOrderData


class Exchange:
    def __init__(self, exchange_id: str, config: dict):
        self.exchange: BaseExchange = getattr(ccxtpro, exchange_id)(config)
        self.orders = bidict()  # id by client_order_id

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_order_book(self, symbol: str, limit: int):
        orderbook = await self.exchange.fetch_order_book(symbol, limit)
        orderbook["timestamp"] *= 1000  # ms to us
        return orderbook

    async def watch_order_book(self, symbol: str, limit: int):
        if self.exchange.has.get("watchOrderBook"):
            return await self.exchange.watch_order_book(symbol, limit)
        return await self.fetch_order_book(symbol, limit)

    async def fetch_partial_balance(self, parts: list[str]):
        balance = await self.exchange.fetch_balance()
        return self._get_partial_balance(balance, parts)

    async def watch_partial_balance(self, parts: list[str]):
        if self.exchange.has.get("watchBalance"):
            balance = await self.exchange.watch_balance()
            return self._get_partial_balance(balance, parts)
        return await self.fetch_partial_balance(parts)

    @staticmethod
    def _get_partial_balance(balance, parts: list[str]):
        default = {"free": 0.0, "used": 0.0, "total": 0.0}
        partial_balance = {part: balance.get(part, default) for part in parts}
        partial_balance["timestamp"] = balance.get("timestamp")
        return partial_balance

    async def fetch_order(self, data: FetchOrderData):
        order_id = self.orders[data["client_order_id"]]
        order = await self.exchange.fetch_order(order_id, data["symbol"])
        order["client_order_id"] = data["client_order_id"]
        return order

    async def _fetch_open_orders(self, symbols: list[str]):
        tasks = [self.exchange.fetch_open_orders(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks)
        return list(itertools.chain.from_iterable(results))

    async def watch_orders(self):
        order = await self.exchange.watch_orders()
        order["client_order_id"] = self.orders.inverse[order["id"]]
        return order

    async def create_order(self, data: CreateOrderData):
        order = await self.exchange.create_order(
            data["symbol"],
            data["type"],
            data["side"],
            data["amount"],
            data["price"],
        )
        self.orders[data["client_order_id"]] = order["id"]
        return order

    async def create_orders(self, orders: list[CreateOrderData]):
        tasks = [self.create_order(order) for order in orders]
        return await asyncio.gather(*tasks)

    async def cancel_order(self, order: FetchOrderData):
        order_id = self.orders[order["client_order_id"]]
        return await self.exchange.cancel_order(order_id, order["symbol"])

    async def cancel_orders(self, orders: list[FetchOrderData]):
        tasks = [self.cancel_order(order) for order in orders]
        return await asyncio.gather(*tasks)

    async def cancel_all_orders(self, symbols: list[str]):
        orders = await self._fetch_open_orders(symbols)
        return await self.cancel_orders(orders)

    async def close(self):
        await self.exchange.close()
