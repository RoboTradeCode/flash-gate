from enum import Enum


class EventType(str, Enum):
    """
    Тип события. Используется при анализе запросов и формировании ответов
    """

    COMMAND = "command"
    DATA = "data"
    ERROR = "error"


class EventAction(str, Enum):
    """
    Команда. Используется при анализе запросов и формировании ответов
    """

    GET_BALANCE = "get_balance"
    CREATE_ORDERS = "create_orders"
    CANCEL_ORDERS = "cancel_orders"
    CANCEL_ALL_ORDERS = "cancel_all_orders"
    GET_ORDERS = "get_orders"
    ORDER_BOOK_UPDATE = "order_book_update"
    BALANCE_UPDATE = "balance_update"
    ORDERS_UPDATE = "orders_update"
    PING = "ping"
