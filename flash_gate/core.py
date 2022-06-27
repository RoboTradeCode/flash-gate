import json
import logging
from typing import Callable
import aeron
from aeron import Subscriber, Publisher
from .enums import Action


class Core:
    def __init__(self, config: dict, handler: Callable[[str], None]):
        aeron_config: dict = config["data"]["configs"]["gate_config"]["aeron"]
        subscribers: dict = aeron_config["subscribers"]
        publishers: dict = aeron_config["publishers"]

        self.logger = logging.getLogger(__name__)
        self.subscriber = Subscriber(handler, **subscribers["core"])
        self.orderbooks = Publisher(**publishers["orderbooks"])
        self.balances = Publisher(**publishers["balances"])
        self.core = Publisher(**publishers["core"])

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def poll(self):
        return self.subscriber.poll()

    async def offer(self, event: dict):
        # Выбор потока для публикации сообщения
        match event["action"]:
            case Action.ORDER_BOOK_UPDATE:
                publisher = self.orderbooks
            case Action.GET_BALANCE | Action.BALANCE_UPDATE:
                publisher = self.balances
            case _:
                publisher = self.core

        # Отправка сообщения в выбранный поток
        message = json.dumps(event)
        return await self._offer(publisher, message)

    async def _offer(self, publisher: Publisher, message: str):
        while True:
            try:
                self.logger.info("Offering message to Core: %s", message)
                result = publisher.offer(message)
                self.logger.info("Message has been offered to Core:", result)
                return result
            except aeron.AeronPublicationNotConnectedError as e:
                self.logger.warning(str(e))
                break
            except aeron.AeronPublicationAdminActionError as e:
                self.logger.warning(str(e))

    async def close(self):
        self.subscriber.close()
        self.orderbooks.close()
        self.balances.close()
        self.core.close()
