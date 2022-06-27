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
