from enum import Enum, auto


class Event(str, Enum):
    COMMAND = "command"
    DATA = "data"
    ERROR = "error"


class Node(str, Enum):
    CONFIGURATOR = "configurator"
    CORE = "core"
    GATE = "gate"
    AGENT = "agent"


class Action(str, Enum):
    GET_BALANCE = "get_balance"
    CREATE_ORDERS = "create_orders"
    CANCEL_ORDERS = "cancel_orders"
    CANCEL_ALL_ORDERS = "cancel_all_orders"
    GET_ORDERS = "get_orders"
    ORDER_BOOK_UPDATE = "order_book_update"
    BALANCE_UPDATE = "balance_update"
    ORDERS_UPDATE = "orders_update"
    PING = "ping"


class Channel(Enum):
    ORDERBOOKS = 1
    BALANCES = 2
    CORE = 3
