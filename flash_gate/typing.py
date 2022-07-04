from typing import Any
from typing import TypedDict, Type
from .enums import EventType, EventAction, EventNode


class OrderBook(TypedDict):
    symbol: str
    bids: list
    asks: list
    timestamp: int


class Balance(TypedDict):
    assets: list
    timestamp: int


class FetchOrderData(TypedDict):
    client_order_id: str
    symbol: str


class CreateOrderData(FetchOrderData):
    type: str
    side: str
    amount: float
    price: float


CreateOrdersData = list[CreateOrderData]
CancelOrdersData = list[FetchOrderData]
GetOrdersData = list[FetchOrderData]


class Order(CreateOrderData):
    id: str
    status: str
    filled: float
    timestamp: int


class Message(TypedDict):
    event_id: str
    event: EventType
    action: EventAction
    message: str
    data: Any


class Event(TypedDict, total=False):
    event_id: str
    event: EventType
    exchange: str
    node: EventNode
    instance: str
    algo: str
    action: EventAction
    message: str
    timestamp: int
    data: Any
