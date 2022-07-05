import itertools
import logging
from abc import ABC, abstractmethod
import ccxtpro
from bidict import bidict
from .enums import StructureType
from .formatters import CcxtFormatterFactory
from .types import OrderBook, Balance, Order, FetchOrderParams, CreateOrderParams


class Exchange(ABC):
    @abstractmethod
    async def fetch_order_book(self, symbol: str, limit: str) -> OrderBook:
        ...

    @abstractmethod
    async def watch_order_book(self, symbol: str, limit: str) -> OrderBook:
        ...

    @abstractmethod
    async def fetch_partial_balance(self, parts: list[str]) -> Balance:
        ...

    @abstractmethod
    async def watch_partial_balance(self, parts: list[str]) -> Balance:
        ...

    @abstractmethod
    async def fetch_order(self, params: FetchOrderParams) -> Order:
        ...

    async def watch_orders(self) -> list[Order]:
        ...

    @abstractmethod
    async def fetch_open_orders(self, symbols: list[str]) -> list[Order]:
        ...

    async def create_orders(self, orders: list[CreateOrderParams]) -> list[Order]:
        ...

    @abstractmethod
    async def cancel_all_orders(self, symbols: list[str]) -> list[Order]:
        ...

    @abstractmethod
    async def cancel_orders(self, orders: list[FetchOrderParams]) -> list[Order]:
        ...


class CcxtExchange(Exchange):
    def __init__(self, exchange_id: str, config: dict):
        self.logger = logging.getLogger()
        self.exchange: ccxtpro.Exchange = getattr(ccxtpro, exchange_id)(config)
        self.id_by_client_order_id = bidict()

    async def fetch_order_book(self, symbol: str, limit: int) -> OrderBook:
        raw_order_book = await self.exchange.fetch_order_book(symbol, limit)
        order_book = await self._format(raw_order_book, StructureType.ORDER_BOOK)
        return order_book

    async def watch_order_book(self, symbol: str, limit: int) -> OrderBook:
        raw_order_book = await self.exchange.watch_order_book(symbol, limit)
        order_book = await self._format(raw_order_book, StructureType.ORDER_BOOK)
        return order_book

    async def fetch_partial_balance(self, parts: list[str]) -> Balance:
        raw_balance = await self.exchange.fetch_balance()
        raw_partial_balance = self._get_partial_balance(raw_balance, parts)
        balance = await self._format(raw_partial_balance, StructureType.BALANCE)
        return balance

    async def watch_partial_balance(self, parts: list[str]) -> Balance:
        raw_balance = await self.exchange.watch_balance()
        raw_partial_balance = self._get_partial_balance(raw_balance, parts)
        balance = await self._format(raw_partial_balance, StructureType.BALANCE)
        return balance

    @staticmethod
    def _get_partial_balance(raw_balance: dict, parts: list[str]) -> dict:
        default = {"free": 0.0, "used": 0.0, "total": 0.0}
        partial_balance = {part: raw_balance.get(part, default) for part in parts}
        return partial_balance

    async def fetch_order(self, params: FetchOrderParams) -> Order:
        order_id = self._get_id_by_client_order_id(params["client_order_id"])
        raw_order = await self.exchange.fetch_order(order_id, params["symbol"])
        order = self._format(raw_order, StructureType.ORDER)
        return order

    async def _get_id_by_client_order_id(self, client_order_id: str) -> str:
        if order_id := self.id_by_client_order_id.get(client_order_id):
            return order_id
        raise ValueError(f"Unknown client order id: {client_order_id}")

    async def fetch_open_orders(self, symbols: list[str]) -> list[Order]:
        raw_orders = await self._fetch_open_orders(symbols)
        orders = [self._format(order, StructureType.ORDER) for order in raw_orders]
        return orders

    async def watch_orders(self) -> list[Order]:
        raw_orders = await self.exchange.watch_orders()
        orders = [self._format(order, StructureType.ORDER) for order in raw_orders]
        return orders

    async def create_orders(self, orders: list[CreateOrderParams]) -> list[Order]:
        orders = [await self._create_order(order) for order in orders]
        return orders

    async def _create_order(self, params: CreateOrderParams) -> Order:
        raw_order = await self.exchange.create_order(
            params["symbol"],
            params["type"],
            params["side"],
            params["amount"],
            params["price"],
        )
        self.id_by_client_order_id[params["client_order_id"]] = raw_order["id"]
        order = self._format(raw_order, StructureType.ORDER)
        return order

    async def cancel_orders(self, orders: list[FetchOrderParams]) -> None:
        for order in orders:
            await self._cancel_order(order)

    async def _cancel_order(self, order: FetchOrderParams) -> None:
        order_id = self.id_by_client_order_id[order["client_order_id"]]
        await self.exchange.cancel_order(order_id, order["symbol"])

    async def cancel_all_orders(self, symbols: list[str]) -> None:
        raw_orders = await self._fetch_open_orders(symbols)
        for raw_order in raw_orders:
            await self.exchange.cancel_order(raw_order["id"], raw_order["symbol"])

    async def _fetch_open_orders(self, symbols: list[str]) -> list[dict]:
        raw_orders_groups = [await self.exchange.fetch_open_orders(s) for s in symbols]
        raw_orders = list(itertools.chain.from_iterable(raw_orders_groups))
        return raw_orders

    @staticmethod
    def _format(ccxt_structure: dict, ccxt_structure_type: StructureType):
        factory = CcxtFormatterFactory()
        formatter = factory.make_formatter(ccxt_structure_type)
        structure = formatter.format(ccxt_structure)
        return structure

    async def close(self) -> None:
        await self.exchange.close()
