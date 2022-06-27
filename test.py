from ccxtpro import kuna
import asyncio
from asyncio import get_running_loop


async def main():
    exchange = kuna(
        {
            "apiKey": "hNvghKfuZvZJftJY1fQskQ1t1wYyx2BxoblhBtXi",
            "secret": "tzSP6gSIlSz3IwbKN2UroLCDtyhMSxJQwU3swPJB",
            "asyncio_loop": get_running_loop(),
        }
    )

    try:
        data = await exchange.create_order("BTC/USDT", "limit", "sell", 0.00001, 100000)
        print(data)
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
