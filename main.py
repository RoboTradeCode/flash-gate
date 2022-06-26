import asyncio
import logging.config
from configparser import ConfigParser
import yaml
from flash_gate import Configurator, Gate

LOGGING_FNAME = "logging.yaml"  # Конфигурация модуля ведения журнала
CONFIG_FILENAME = "config.ini"  # Начальная конфигурация


async def main():
    # Настройка модуля ведения журнала
    with open(LOGGING_FNAME) as f:
        d = yaml.safe_load(f)
        logging.config.dictConfig(d)

    # Получение начальной конфигурации
    ini = ConfigParser()
    ini.read(CONFIG_FILENAME)

    # Получение основной конфигурации
    async with Configurator(ini) as configurator:
        config = await configurator.get_config()

    # Запуск шлюза
    async with Gate(config) as gate:
        await gate.run()


if __name__ == "__main__":
    asyncio.run(main())
