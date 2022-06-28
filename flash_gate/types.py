from typing import TypedDict


class FetchOrderData(TypedDict):
    client_order_id: str
    symbol: str


class CreateOrderData(TypedDict):
    client_order_id: str
    symbol: str
    type: str
    side: str
    price: float
    amount: float


class OrderBook(TypedDict):
    bids: list
    asks: list
    symbol: str
    timestamp: int


class Asset(TypedDict):
    free: float
    used: float
    total: float


class Balance(TypedDict):
    assets: list[Asset]
    timestamp: str


class Order(TypedDict):
    symbol: str
    type: str
    side: str
    amount: float
    price: float
    client_order_id: str
