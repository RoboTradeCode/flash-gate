import pytest
from flash_gate.exchange import Exchange
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.fixture(scope="session")
async def exchange():
    api_key = "hNvghKfuZvZJftJY1fQskQ1t1wYyx2BxoblhBtXi"
    secret = "tzSP6gSIlSz3IwbKN2UroLCDtyhMSxJQwU3swPJB"
    exchange = Exchange("kuna", {"apiKey": api_key, "secret": secret})
    yield exchange
    await exchange.close()
