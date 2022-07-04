import pytest
import data
from flash_gate.exchange.exchange import Exchange


class TestExchangeClass:
    @staticmethod
    def test_order_keys():
        assert set(Exchange.ORDER_KEYS) == data.ORDER_KEYS

    @staticmethod
    def test_filter_keys():
        filtered = Exchange._filter_keys({"a": "1", "b": 2}, ["Ni!"])
        return filtered == {"Ni!": 8}

    @staticmethod
    def test_fill_empty_keys():
        dictionary = {"Spam!": None, "Ni!": 8}
        data = {"Spam!": "Bacon", "Grenade": "HolyHand"}
        filled = Exchange._fill_empty_keys(dictionary, data)
        assert filled == {"Spam!": "Bacon", "Ni!": 8}

    @staticmethod
    def test_convert_ms_to_us():
        assert Exchange._convert_ms_to_us(1656804328000) == 1656804328000000


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
