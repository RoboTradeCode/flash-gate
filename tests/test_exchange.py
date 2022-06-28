import pytest
from flash_gate.types import CreateOrderData, FetchOrderData


ORDER_BOOK_SYMBOL = "BTC/USDT"
ORDER_BOOK_LIMIT = 1
ORDER_BOOK_KEYS = ["bids", "asks", "symbol", "timestamp"]
ORDER_BOOK_TYPES = [list, list, str, int]
BALANCE_PARTS = ["BTC"]
ORDER_KEYS = ["symbol", "type", "side", "amount", "price", "client_order_id"]
ORDER_TYPES = [str, str, str, float, float, str]
CREATE_ORDER_DATA: CreateOrderData = {
    "client_order_id": "573911bd-7a22-4126-81b0-8f1bdb7ea499",
    "symbol": "BTC/USDT",
    "type": "limit",
    "side": "sell",
    "price": 1000000,
    "amount": 0.00001,
}
FETCH_ORDER_DATA: FetchOrderData = {
    "client_order_id": "573911bd-7a22-4126-81b0-8f1bdb7ea499",
    "symbol": "BTC/USDT",
}


@pytest.mark.asyncio
@pytest.fixture(scope="session", params=["fetch", "watch"])
async def order_book(request, exchange):
    match request.param:
        case "fetch":
            method = exchange.fetch_order_book
        case _:
            method = exchange.watch_order_book

    yield await method(ORDER_BOOK_SYMBOL, ORDER_BOOK_LIMIT)


@pytest.mark.asyncio
@pytest.fixture(scope="session", params=["fetch", "watch"])
async def balance(request, exchange):
    match request.param:
        case "fetch":
            method = exchange.fetch_balance
        case _:
            method = exchange.watch_balance

    yield await method(BALANCE_PARTS)


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def order(exchange):
    yield await exchange.create_orders([CREATE_ORDER_DATA])
    yield await exchange.watch_orders()
    yield await exchange.fetch_order(FETCH_ORDER_DATA)


class TestOrderBook:
    def test_order_book_is_dict(self, order_book):
        assert isinstance(order_book, dict)

    @pytest.mark.parametrize("key", ORDER_BOOK_KEYS)
    def test_order_book_has_key(self, order_book, key):
        assert key in order_book

    def test_order_book_has_not_additional_keys(self, order_book):
        assert set(order_book) - set(ORDER_BOOK_KEYS)

    @pytest.mark.parametrize("key,cls", zip(ORDER_BOOK_KEYS, ORDER_BOOK_TYPES))
    def test_order_book_key_is_instance(self, order_book, key, cls):
        assert isinstance(order_book[key], cls)

    def test_order_book_contains_requested_symbol(self, order_book):
        assert order_book["symbol"] == ORDER_BOOK_SYMBOL

    @pytest.mark.parametrize("side", ["bids", "asks"])
    def test_order_book_order_length_equals_limit(self, order_book, side):
        assert len(order_book[side]) == ORDER_BOOK_LIMIT

    @pytest.mark.parametrize("side", ["bids", "asks"])
    def test_order_book_order_contains_2_values(self, order_book, side):
        assert all(len(order) == 2 for order in order_book[side])

    @pytest.mark.parametrize("side", ["bids", "asks"])
    def test_order_book_order_value_is_float(self, order_book, side):
        orders = order_book[side]
        assert all(isinstance(value, float) for order in orders for value in order)

    def test_order_book_timestamp_contains_16_digits(self, order_book):
        assert len(str(order_book["timestamp"])) == 16


class TestBalance:
    def test_balance_is_dict(self, balance):
        assert isinstance(balance, dict)

    def test_balance_asset_is_dict(self, balance):
        balance = dict(balance)
        balance.pop("timestamp", None)
        assert all(isinstance(value, dict) for asset, value in balance.items())

    @pytest.mark.parametrize("key", ["free", "used", "total"])
    def test_balance_asset_has_key(self, balance, key):
        balance = dict(balance)
        balance.pop("timestamp", None)
        assert all(key in value for asset, value in balance.items())

    def test_balance_currency_contains_3_values(self, balance):
        balance = dict(balance)
        balance.pop("timestamp", None)
        assert all(len(value) == 3 for currency, value in balance.items())

    def test_balance_has_timestamp(self, balance):
        assert "timestamp" in balance

    def test_balance_timestamp_is_optional_int(self, balance):
        timestamp = balance["timestamp"]
        assert timestamp is None or isinstance(timestamp, int)

    def test_balance_timestamp_contains_16_digits_if_is_not_none(self, balance):
        timestamp = balance["timestamp"]
        if timestamp is not None:
            assert len(str(timestamp)) == 16


class TestOrder:
    def test_order_is_dict(self, order):
        assert isinstance(order, dict)

    @pytest.mark.parametrize("key", ORDER_KEYS)
    def test_order_has_key(self, order, key):
        assert key in order

    def test_order_has_not_additional_keys(self, order):
        assert set(order) - set(ORDER_KEYS)

    @pytest.mark.parametrize("key,cls", zip(ORDER_KEYS, ORDER_TYPES))
    def test_order_key_is_instance(self, order, key, cls):
        assert isinstance(order[key], cls)

    #
    # def test_order_book_contains_requested_symbol(self, order_book):
    #     assert order_book["symbol"] == ORDER_BOOK_SYMBOL

    def test_order_timestamp_contains_16_digits(self, order):
        assert len(str(order["timestamp"])) == 16
