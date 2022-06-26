import logging
from configparser import ConfigParser
from aiohttp import ClientSession


class Configurator:
    def __init__(self, config: ConfigParser):
        self.logger = logging.getLogger(__name__)
        self.session = ClientSession(config.get("configurator", "base_url"))
        self.exchange_id = config.get("configurator", "exchange_id")
        self.instance = config.get("configurator", "instance")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_config(self) -> dict:
        # Возвращать полную конфигурацию
        params = {"only_new": "false"}

        self.logger.info("Trying to get config: %s", self._method)
        async with self.session.get(await self._method, params=params) as response:
            config = await response.json()

        self.logger.info("Received config: %s", config)
        return config

    @property
    async def _method(self):
        return f"/{self.exchange_id}/{self.instance}"

    async def close(self):
        await self.session.close()
