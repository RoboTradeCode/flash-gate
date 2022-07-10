import asyncio
import logging.config
from configparser import ConfigParser
import yaml
from flash_gate import Configurator, Gate

LOGGING_FNAME = "logging.yaml"
CONFIG_FILENAME = "config.ini"


async def main():
    with open(LOGGING_FNAME) as f:
        d = yaml.safe_load(f)
        logging.config.dictConfig(d)

    ini = ConfigParser()
    ini.read(CONFIG_FILENAME)
    configurator_driver_type = ini.get("configurator", "type")
    configurator_source = ini.get("configurator", "source")

    configurator = Configurator(configurator_driver_type, configurator_source)
    config = configurator.get_config()

    config = await configurator.get_config()

    async with Gate(config) as gate:
        await gate.run()


if __name__ == "__main__":
    asyncio.run(main())
