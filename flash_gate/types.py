from typing import TypedDict


class FetchOrderData(TypedDict):
    client_order_id: str
    symbol: str


class OrderBook(TypedDict):
    bids: list
    asks: list
    symbol: str
    timestamp: int


class Balance(TypedDict):
    assets: list
    timestamp: str


class Order(TypedDict):
    client_order_id: str
    symbol: str
    type: str
    side: str
    amount: float
    price: float
