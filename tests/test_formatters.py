from flash_gate.formatters import Formatter
import pytest
import json
import data.order_book


@pytest.fixture
def formatter():
    with open("data/config.json") as f:
        config = json.load(f)
        return Formatter(config)


class TestFormatter:
    def test_order_book(self, formatter: Formatter):
        data = data.order_book.CCXT
        order_book = data.order_book.ROBO_TRADE_CODE
        formatted_order_book = formatter._format_order_book(ccxt_order_book)

        assert formatted_order_book == order_book

    def test_orders(self, formatter: Formatter):
        ccxt_orders = data.orders.CCXT
        orders = data.orders.ROBO_TRADE_CODE
        formatted_orders = formatter._format_orders()

        assert formatted_order_book == order_book

    def test_balance(formatter: Formatter):
        ccxt_order_book = data.order_book.CCXT
        order_book = data.order_book.ROBO_TRADE_CODE
        formatted_order_book = formatter._format_order_book(ccxt_order_book)

        assert formatted_order_book == order_book
