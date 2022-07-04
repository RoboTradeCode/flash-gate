import datetime
import itertools
from datetime import datetime
from typing import Callable, Optional, Awaitable
import ccxtpro
from bidict import bidict
from ccxtpro import Exchange as BaseExchange
from .enums import CcxtStructure
from .formatters import Formatter, OrderBookFormatter
from .typing import OrderBook, Balance, Order


class Exchange:
    def __init__(self, exchange_id: str, config: dict):
        self.exchange: BaseExchange = getattr(ccxtpro, exchange_id)(config)
        self.id_by_client_order_id = bidict()
        self.last_balance_timestamp = 0

    async def fetch_order_book(self, symbol: str, limit: int) -> OrderBook:
        method = await self.exchange.fetch_order_book(symbol, limit)
        order_book = await self._get_order_book(method)
        return order_book

    async def watch_order_book(self, symbol: str, limit: int) -> OrderBook:
        method = await self.exchange.watch_order_book(symbol, limit)
        order_book = await self._get_order_book(method)
        return order_book

    async def _get_order_book(self, method: Awaitable) -> OrderBook:
        raw_order_book = await method
        order_book = self._format(raw_order_book, CcxtStructure.ORDER_BOOK)
        return order_book

    def _format(self, ccxt_structure, ccxt_structure_type: CcxtStructure):
        formatter = self._get_formatter()
        return formatter.format(data)

    @staticmethod
    def _get_formatter(ccxt_structure_type: CcxtStructure) -> Formatter:
        match ccxt_structure_type:
            case _:
                return OrderBookFormatter()

    def _format_raw_order_book(self, raw_order_book: dict) -> OrderBook:
        order_book = self._filter_keys(raw_order_book, self.ORDER_BOOK_KEYS)
        order_book["timestamp"] = self._get_timestamp_in_us(order_book)
        return order_book

    async def fetch_balance(self, assets: list[str]) -> Balance:
        raw_balance = await self._get_actual_balance(self.exchange.fetch_balance)
        balance = self._format_raw_balance(raw_balance, assets)
        return balance

    async def watch_balance(self, assets: list[str]) -> Balance:
        raw_balance = await self._get_actual_balance(self.exchange.watch_balance)
        balance = self._format_raw_balance(raw_balance, assets)
        return balance

    async def _get_actual_balance(self, method: Callable) -> dict:
        while True:
            raw_balance = await method()
            timestamp = raw_balance.get("timestamp", datetime.now().timestamp())
            if timestamp > self.last_balance_timestamp:
                self.last_balance_timestamp = timestamp
                break

        return raw_balance

    def _format_raw_balance(self, raw_balance: dict, parts: list[str]) -> Balance:
        balance = dict()
        balance["assets"] = self._get_partial_balance(raw_balance, parts)
        balance["timestamp"] = self._get_timestamp_in_us(raw_balance)
        return balance

    @staticmethod
    def _get_partial_balance(raw_balance: dict, parts: list[str]) -> dict:
        default = {"free": 0.0, "used": 0.0, "total": 0.0}
        partial_balance = {part: raw_balance.get(part, default) for part in parts}
        return partial_balance

    def _get_timestamp_in_us(self, raw: dict) -> Optional[int]:
        if timestamp_in_ms := raw.get("timestamp"):
            return self._convert_ms_to_us(timestamp_in_ms)

    async def fetch_orders(self, symbols: list[str]) -> list[Order]:
        raw_orders = await self._fetch_open_orders(symbols)
        orders = self._format_raw_orders(raw_orders)
        return orders

    async def fetch_order(self, data: FetchOrderData) -> Order:
        order_id = self.id_by_client_order_id[data["client_order_id"]]
        raw_order = await self.exchange.fetch_order(order_id, data["symbol"])
        order = self._format_raw_order(raw_order)
        return order

    async def watch_orders(self) -> list[Order]:
        raw_orders = await self.exchange.watch_orders()
        orders = self._format_raw_orders(raw_orders)
        return orders

    async def create_orders(self, orders: list[CreateOrderData]) -> list[Order]:
        orders = [await self._create_order(order) for order in orders]
        return orders

    async def _create_order(self, data: CreateOrderData) -> Order:
        raw_order = await self.exchange.create_order(
            data["symbol"],
            data["type"],
            data["side"],
            data["amount"],
            data["price"],
        )
        self.id_by_client_order_id[data["client_order_id"]] = raw_order["id"]
        order = self._format_raw_order(raw_order, data)
        return order

    def _format_raw_orders(self, raw_orders: list) -> list[Order]:
        orders = [self._format_raw_order(raw_order) for raw_order in raw_orders]
        return orders

    def _format_raw_order(self, raw_order: dict, data: CreateOrderData = None) -> Order:
        # Default argument value is mutable
        if data is None:
            data = {}

        order = self._filter_keys(raw_order, self.ORDER_KEYS)
        order = self._fill_empty_keys(order, data)
        order["client_order_id"] = self.id_by_client_order_id.inverse[order["id"]]
        order["timestamp"] = self._convert_ms_to_us(order["timestamp"])
        return order

    @staticmethod
    def _filter_keys(dictionary: dict, keys: list[str]) -> dict:
        return {key: dictionary.get(key) for key in keys}

    @staticmethod
    def _fill_empty_keys(dictionary: dict, data: dict) -> dict:
        filled_dict = dictionary.copy()
        empty_keys = [key for key, value in dictionary.items() if value is None]
        filled_dict.update((key, data.get(key)) for key in empty_keys)
        return filled_dict

    @staticmethod
    def _convert_ms_to_us(ms: int) -> int:
        return ms * 1000

    async def cancel_orders(self, orders: list[FetchOrderData]) -> None:
        for order in orders:
            await self._cancel_order(order)

    async def _cancel_order(self, order: FetchOrderData) -> None:
        order_id = self.id_by_client_order_id[order["client_order_id"]]
        await self.exchange.cancel_order(order_id, order["symbol"])

    async def cancel_all_orders(self, symbols: list[str]) -> None:
        orders = await self._fetch_open_orders(symbols)
        for order in orders:
            await self.exchange.cancel_order(order["id"], order["symbol"])

    async def _fetch_open_orders(self, symbols: list[str]) -> list:
        order_groups = [await self.exchange.fetch_open_orders(s) for s in symbols]
        orders = list(itertools.chain.from_iterable(order_groups))
        return orders

    async def close(self) -> None:
        await self.exchange.close()
