import asyncio
from flash_gate import Configurator


async def main():
    source = "https://configurator.robotrade.io/kucoin/1?only_new=false"
    async with Configurator(source) as configurator:
        config = await configurator.get_config()

    print(config)


if __name__ == "__main__":
    asyncio.run(main())
