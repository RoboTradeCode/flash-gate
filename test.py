import asyncio
from ccxtpro import exmo
import logging


async def main():
    logging.basicConfig(level=logging.DEBUG)

    api_key = "K-5c48ca01887ddf50ea7094e021b1f37c37ced971"
    secret = "S-127383e2a3cc853a0be497520de08029d1016b9f"
    exchange = exmo({"apiKey": api_key, "secret": secret})

    try:
        balance_before = await exchange.fetch_balance()
        created_order = await exchange.create_order(
            "BTC/USDT", "market", "sell", 0.0001, 100000
        )
        fetched_order = await exchange.fetch_order(created_order["id"])
        balance_after = await exchange.fetch_balance()

        print(f"Balance before: {balance_before}")
        print(f"Created order: {created_order}")
        print(f"Fetched order: {fetched_order}")
        print(f"Balance after: {balance_after}")
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
