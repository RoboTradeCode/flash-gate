import logging
from aiohttp import ClientSession
from configparser import ConfigParser


class Configurator:
    def __init__(self, config: ConfigParser):
        self.logger = logging.getLogger(__name__)
        self.session = ClientSession()
        self.url = config.get("configuration", "source")

    async def get_config(self) -> dict:
        self.logger.info("Trying to get config...")
        async with self.session.get(self.url) as response:
            config = await response.json()

        self.logger.info("Received config: %s", config)
        return config

    async def close(self):
        await self.session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
