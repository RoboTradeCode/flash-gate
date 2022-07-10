from flash_gate import Configurator
import asyncio
import logging.config
import yaml

LOGGING_FNAME = "logging.yaml"


async def main():
    with open(LOGGING_FNAME) as f:
        d = yaml.safe_load(f)
        logging.config.dictConfig(d)

    driver_type = "api"
    source = "https://configurator.robotrade.io/exmo/test?only_new=false"

    # noinspection PyTypeChecker
    configurator = Configurator(driver_type, source)

    config = await configurator.get_config()
    print(config)


if __name__ == "__main__":
    asyncio.run(main())
