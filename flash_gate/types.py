from typing import TypedDict
from enums import Event, Action
from typing import Any


class OrderBook(TypedDict):
    bids: list
    asks: list
    symbol: str
    timestamp: int


class Balance(TypedDict):
    assets: list
    timestamp: str


class FetchOrderData(TypedDict):
    client_order_id: str
    symbol: str


class CreateOrderData(FetchOrderData):
    type: str
    side: str
    amount: float
    price: float


class Order(CreateOrderData):
    id: str
    status: str
    filled: float
    timestamp: int


class Message(TypedDict):
    event_id: str
    event: Event
    action: Action
    message: str
    data: Any
