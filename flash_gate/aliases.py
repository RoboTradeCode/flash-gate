from ccxtpro import Exchange
from typing import Type, TypedDict


BaseExchange = Type[Exchange]


class CreatedOrder(TypedDict):
    id: str
    symbol: str


class CreatingOrder(TypedDict):
    symbol: str
    type: str
    side: str
    price: float
    amount: float
