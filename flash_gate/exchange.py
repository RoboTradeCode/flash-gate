import asyncio
import itertools
from asyncio import get_running_loop
import ccxtpro
from .aliases import BaseExchange, CreatedOrder, CreatingOrder


class Exchange:
    def __init__(self, config: dict):
        gate_config: dict = config["data"]["configs"]["gate_config"]
        exchange_id: str = gate_config["info"]["exchange"]
        exchange_cls: BaseExchange = getattr(ccxtpro, exchange_id)
        exchange_config = {
            "apiKey": gate_config["api_key"],
            "secret": gate_config["secret_key"],
            "password": gate_config["password"],
            "asyncio_loop": get_running_loop(),
            "enableRateLimit": gate_config["rate_limits"]["enable_ccxt_rate_limiter"],
        }

        self.exchange = exchange_cls(exchange_config)
        self.exchange.check_required_credentials()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def fetch_order_book(self, symbol: str, limit: int):
        if self.exchange.has.get("fetchOrderBook"):
            return await self.exchange.fetch_order_book(symbol, limit)
        raise NotImplementedError

    async def watch_order_book(self, symbol: str, limit: int):
        if self.exchange.has.get("watchOrderBook"):
            return await self.exchange.watch_order_book(symbol, limit)
        raise NotImplementedError

    async def fetch_balance(self):
        if self.exchange.has.get("fetchBalance"):
            return await self.exchange.fetch_balance()
        raise NotImplementedError

    async def watch_balance(self):
        if self.exchange.has.get("watchBalance"):
            return await self.exchange.watch_balance()
        raise NotImplementedError

    async def fetch_order(self, order: CreatedOrder):
        if self.exchange.has.get("fetchOrder"):
            return await self.exchange.fetch_order(order["id"], order["symbol"])
        raise NotImplementedError

    async def fetch_orders(self, symbols: list[str]):
        if self.exchange.has.get("fetchOpenOrders"):
            tasks = [self.exchange.fetch_open_orders(symbol) for symbol in symbols]
            results = await asyncio.gather(*tasks)
            return list(itertools.chain.from_iterable(results))
        raise NotImplementedError

    async def watch_orders(self):
        if self.exchange.has.get("watchOrders"):
            return await self.exchange.watch_orders()
        raise NotImplementedError

    async def create_order(self, order: CreatingOrder):
        return await self.exchange.create_order(
            order["symbol"],
            order["type"],
            order["side"],
            order["amount"],
            order["price"],
        )

    async def create_orders(self, orders: list[CreatingOrder]):
        tasks = [self.create_order(order) for order in orders]
        return await asyncio.gather(*tasks)

    async def cancel_order(self, order: CreatedOrder):
        return await self.exchange.cancel_order(order["id"], order["symbol"])

    async def cancel_orders(self, orders: list[CreatedOrder]):
        tasks = [self.cancel_order(order) for order in orders]
        return await asyncio.gather(*tasks)

    async def cancel_all_orders(self, symbols: list[str]):
        orders = await self.fetch_orders(symbols)
        return await self.cancel_orders(orders)

    async def close(self):
        await self.exchange.close()
