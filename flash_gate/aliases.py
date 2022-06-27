from ccxtpro import Exchange
from typing import Type, TypedDict


BaseExchange = Type[Exchange]


class CreatingOrder(TypedDict):
    symbol: str
    type: str
    side: str
    price: float
    amount: float
    client_order_id: str
