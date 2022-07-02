from asyncio import get_running_loop
import pytest
from flash_gate.exchange import Exchange


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
async def order_book(exchange):
    return {}
