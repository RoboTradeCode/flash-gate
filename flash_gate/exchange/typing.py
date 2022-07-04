from typing import TypedDict, Optional


class OrderBook(TypedDict):
    bids: list
    asks: list
    symbol: str
    timestamp: Optional[int]


class Balance(TypedDict):
    assets: list
    timestamp: Optional[int]


class Order(TypedDict):
    id: str
    client_order_id: str
    timestamp: int
    status: str
    symbol: str
    type: str
    side: str
    price: float
    amount: float
    filled: float
