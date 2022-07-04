from asyncio import get_running_loop
import pytest
import data
from flash_gate.exchange.exchange import Exchange


@pytest.fixture(scope="session")
def event_loop():
    yield get_running_loop()


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def exchange():
    async with Exchange("", {}) as exchange:
        yield exchange


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def raw_order_book(exchange):
    return data.RAW_ORDER_BOOK
