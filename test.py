import asyncio
from ccxtpro import kuna


async def main():
    api_key = "hNvghKfuZvZJftJY1fQskQ1t1wYyx2BxoblhBtXi"
    secret = "tzSP6gSIlSz3IwbKN2UroLCDtyhMSxJQwU3swPJB"
    exchange = kuna({"apiKey": api_key, "secret": secret})

    order = await exchange.create_order(
        "BTC/USDT", "market", "sell", 100000000000, 100000
    )
    print(order)

    await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
