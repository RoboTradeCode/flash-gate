import asyncio
from asyncio import get_running_loop
from ccxtpro import binance
from pprint import pprint


async def main():
    exchange = binance(
        {
            "apiKey": "Q0LPrj20sAGqptchS8ZiR2kJzUggr5W3CZVRxIRzB8Nr1OSgbXivjF62YVE0E98e",
            "secret": "V9fu4jT21mzejk0sdq3jutubN6xxLMvBtY6ZKRJYXb3kNlYMJfoeTxXG8qDweRek",
            "asyncio_loop": get_running_loop(),
            "enableRateLimit": True,
        }
    )

    try:
        describe = exchange.has
        pprint(describe)
    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())
