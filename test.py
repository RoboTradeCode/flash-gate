import asyncio
from ccxtpro import kuna


async def main():
    api_key = "hNvghKfuZvZJftJY1fQskQ1t1wYyx2BxoblhBtXi"
    secret = "tzSP6gSIlSz3IwbKN2UroLCDtyhMSxJQwU3swPJB"
    exchange = kuna({"apiKey": api_key, "secret": secret})

    # order = await exchange.create_order("BTC/USDT", "limit", "sell", 0.000001, 100000)
    # print(order)
    # orders = await exchange.fetch_open_orders("BTC/USDT")
    # print(orders)
    # await exchange.cancel_order(order["id"], order["symbol"])

    balance = await exchange.fetch_order_book("BTC/USDT")
    print(balance)

    await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
