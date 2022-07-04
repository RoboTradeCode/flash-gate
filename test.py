import asyncio
from flash_gate.exchange import Exchange
from ccxtpro import kuna


async def main():
    api_key = "hNvghKfuZvZJftJY1fQskQ1t1wYyx2BxoblhBtXi"
    secret = "tzSP6gSIlSz3IwbKN2UroLCDtyhMSxJQwU3swPJB"
    exchange = Exchange("kuna", {"apiKey": api_key, "secret": secret})

    order_book = await exchange.fetch_order_book("BTC/USDT", 1)

    print(order_book)
    await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
