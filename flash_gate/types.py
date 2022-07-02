from typing import TypedDict


class OrderBook(TypedDict):
    bids: list
    asks: list
    symbol: str
    timestamp: int


class Balance(TypedDict):
    assets: list
    timestamp: str


class CreateOrderData(TypedDict):
    client_order_id: str
    symbol: str
    type: str
    side: str
    amount: float
    price: float


class Order(CreateOrderData):
    id: str
    filled: float


class FetchOrderData(TypedDict):
    client_order_id: str
    symbol: str


class Message:
    pass
